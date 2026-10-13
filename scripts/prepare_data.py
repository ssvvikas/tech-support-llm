#!/usr/bin/env python3
"""
Fetch tech support Q&A from Stack Exchange (Super User + Server Fault),
clean it, and produce train/valid/test JSONL splits for mlx-lm fine-tuning.

Data is licensed CC BY-SA 4.0 by Stack Exchange contributors.
"""

import json
import re
import time
import random
import sys
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import gzip
import io

# ── Config ──────────────────────────────────────────────────────────────
API_BASE = "https://api.stackexchange.com/2.3"
SITES = ["superuser", "serverfault"]
MIN_SCORE = 3          # question score threshold (stricter filter)
MIN_ANSWER_SCORE = 3   # accepted answer must also have score ≥3
MIN_ANSWER_WORDS = 50  # skip very short answers
MAX_ANSWER_WORDS = 800 # skip mega-long answers (noise for training)
MAX_PAGES_PER_SITE = 80  # up to 8,000 questions checked per site
PAGE_SIZE = 100
API_DELAY = 1.0        # seconds between API calls (be polite)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"

# ── HTML → plain text ───────────────────────────────────────────────────
def html_to_text(html_str: str) -> str:
    """Convert Stack Exchange HTML to clean plain text.
    Keeps code blocks readable, strips everything else."""
    if not html_str:
        return ""
    text = html_str

    # Replace <code> blocks with backtick-wrapped text
    text = re.sub(r"<pre><code>(.*?)</code></pre>", r"\n```\n\1\n```\n", text, flags=re.DOTALL)
    text = re.sub(r"<code>(.*?)</code>", r"`\1`", text, flags=re.DOTALL)

    # Replace common block elements with newlines
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</?(?:p|div|h[1-6]|li|ul|ol|blockquote)(?:\s[^>]*)?>", "\n", text)
    text = re.sub(r"<hr\s*/?>", "\n---\n", text)

    # Replace links: <a href="URL">text</a> → text (URL)
    text = re.sub(r'<a\s+href="([^"]*)"[^>]*>(.*?)</a>', r"\2", text, flags=re.DOTALL)

    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Decode HTML entities
    text = unescape(text)

    # Clean up whitespace: collapse blank lines, trim
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text


# ── Stack Exchange API helpers ──────────────────────────────────────────
def api_get(endpoint: str, params: dict) -> dict:
    """Make a GET request to the Stack Exchange API.
    The API returns gzip-compressed JSON."""
    url = f"{API_BASE}{endpoint}?{urlencode(params)}"
    req = Request(url, headers={"Accept-Encoding": "gzip"})
    with urlopen(req, timeout=30) as resp:
        raw = resp.read()
        # API always gzips the response
        try:
            text = gzip.decompress(raw).decode("utf-8")
        except gzip.BadGzipFile:
            text = raw.decode("utf-8")
    return json.loads(text)


def fetch_questions(site: str) -> list[dict]:
    """Fetch questions with accepted answers and score ≥ MIN_SCORE."""
    questions = []
    page = 1

    while page <= MAX_PAGES_PER_SITE:
        params = {
            "site": site,
            "sort": "votes",
            "order": "desc",
            "min": MIN_SCORE,
            "pagesize": PAGE_SIZE,
            "page": page,
            "filter": "withbody",  # includes question body
        }
        try:
            data = api_get("/questions", params)
        except Exception as e:
            print(f"  API error on page {page}: {e}")
            break

        items = data.get("items", [])
        if not items:
            break

        for q in items:
            if q.get("accepted_answer_id") and q.get("score", 0) >= MIN_SCORE:
                questions.append(q)

        quota = data.get("quota_remaining", 0)
        has_more = data.get("has_more", False)

        print(f"  [{site}] page {page}: got {len(items)} Qs, "
              f"{len(questions)} with accepted answers so far, "
              f"API quota left: {quota}")

        if not has_more or quota < 20:
            if quota < 20:
                print(f"  ⚠ Stopping early — API quota low ({quota})")
            break

        page += 1
        time.sleep(API_DELAY)

    return questions


def fetch_answers_batch(answer_ids: list[int], site: str) -> dict[int, dict]:
    """Fetch answer bodies in batches of 100 (API limit)."""
    answers = {}

    for i in range(0, len(answer_ids), 100):
        batch = answer_ids[i:i + 100]
        ids_str = ";".join(str(aid) for aid in batch)
        params = {
            "site": site,
            "filter": "withbody",
            "pagesize": 100,
        }
        try:
            data = api_get(f"/answers/{ids_str}", params)
        except Exception as e:
            print(f"  Answer fetch error (batch {i // 100 + 1}): {e}")
            continue

        for a in data.get("items", []):
            answers[a["answer_id"]] = a

        quota = data.get("quota_remaining", 0)
        print(f"  Fetched answers batch {i // 100 + 1}/{(len(answer_ids) - 1) // 100 + 1}, "
              f"quota left: {quota}")

        if quota < 20:
            print(f"  ⚠ Stopping answer fetch — quota low ({quota})")
            break

        time.sleep(API_DELAY)

    return answers


# ── Build examples ──────────────────────────────────────────────────────
def build_examples(questions: list[dict], answers: dict[int, dict],
                   site: str) -> list[dict]:
    """Pair questions with their accepted answers, clean, and filter."""
    examples = []
    skipped = {"no_answer": 0, "short_answer": 0, "long_answer": 0,
               "low_answer_score": 0}

    for q in questions:
        aid = q.get("accepted_answer_id")
        if aid not in answers:
            skipped["no_answer"] += 1
            continue

        answer = answers[aid]

        # Filter by answer score
        if answer.get("score", 0) < MIN_ANSWER_SCORE:
            skipped["low_answer_score"] += 1
            continue

        # Clean the text
        q_title = unescape(q.get("title", ""))
        q_body = html_to_text(q.get("body", ""))
        a_body = html_to_text(answer.get("body", ""))

        # Build user message: title + relevant body details
        # Keep it concise — the title is usually the main question
        if q_body and len(q_body) > 20:
            user_msg = f"{q_title}\n\n{q_body}"
        else:
            user_msg = q_title

        # Check answer length
        word_count = len(a_body.split())
        if word_count < MIN_ANSWER_WORDS:
            skipped["short_answer"] += 1
            continue
        if word_count > MAX_ANSWER_WORDS:
            skipped["long_answer"] += 1
            continue

        example = {
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": a_body},
            ],
            "metadata": {
                "source": f"stackexchange/{site}",
                "question_id": q["question_id"],
                "question_score": q["score"],
                "answer_score": answer.get("score", 0),
                "tags": q.get("tags", []),
            },
        }
        examples.append(example)

    print(f"  [{site}] Built {len(examples)} examples. Skipped: {skipped}")
    return examples


# ── Split data ──────────────────────────────────────────────────────────
def split_data(examples: list[dict], seed: int = 42):
    """Shuffle and split 80/10/10 into train/valid/test."""
    rng = random.Random(seed)
    rng.shuffle(examples)

    n = len(examples)
    n_test = max(1, n // 10)
    n_valid = max(1, n // 10)

    test = examples[:n_test]
    valid = examples[n_test:n_test + n_valid]
    train = examples[n_test + n_valid:]

    return train, valid, test


def write_jsonl(data: list[dict], path: Path):
    """Write examples to JSONL. Strip metadata for mlx-lm compatibility."""
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            # mlx-lm expects only {"messages": [...]}
            clean = {"messages": item["messages"]}
            f.write(json.dumps(clean, ensure_ascii=False) + "\n")
    print(f"  Wrote {len(data)} examples → {path.name}")


def write_jsonl_full(data: list[dict], path: Path):
    """Write full examples (with metadata) for reference."""
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"  Wrote {len(data)} examples (with metadata) → {path.name}")


# ── Main ────────────────────────────────────────────────────────────────
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_examples = []

    for site in SITES:
        print(f"\n{'='*60}")
        print(f"Processing: {site}")
        print(f"{'='*60}")

        # Step 1: Fetch questions
        print("Fetching questions...")
        questions = fetch_questions(site)
        print(f"  Found {len(questions)} questions with accepted answers (score ≥{MIN_SCORE})")

        if not questions:
            print("  No questions found, skipping.")
            continue

        # Step 2: Fetch accepted answers
        print("Fetching accepted answers...")
        answer_ids = [q["accepted_answer_id"] for q in questions]
        answers = fetch_answers_batch(answer_ids, site)
        print(f"  Fetched {len(answers)} answers")

        # Step 3: Build examples
        print("Building examples...")
        examples = build_examples(questions, answers, site)
        all_examples.extend(examples)

    print(f"\n{'='*60}")
    print(f"Total examples across all sites: {len(all_examples)}")
    print(f"{'='*60}")

    if not all_examples:
        print("No examples collected. Check API quota and filters.")
        sys.exit(1)

    # Save all examples with metadata (for reference)
    write_jsonl_full(all_examples, OUTPUT_DIR / "all_examples.jsonl")

    # Split and save (without metadata, mlx-lm format)
    train, valid, test = split_data(all_examples)
    write_jsonl(train, OUTPUT_DIR / "train.jsonl")
    write_jsonl(valid, OUTPUT_DIR / "valid.jsonl")
    write_jsonl(test, OUTPUT_DIR / "test.jsonl")

    # Print summary
    print(f"\n{'='*60}")
    print("Done!")
    print(f"  train.jsonl: {len(train)} examples")
    print(f"  valid.jsonl: {len(valid)} examples")
    print(f"  test.jsonl:  {len(test)} examples")
    print(f"  all_examples.jsonl: {len(all_examples)} examples (with metadata)")
    print(f"\nFiles saved to: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
