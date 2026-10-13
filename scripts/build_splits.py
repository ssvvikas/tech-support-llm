#!/usr/bin/env python3
"""
Combine all data sources and create train/valid/test splits.

Usage:
    python scripts/build_splits.py

Reads all .jsonl files in data/ (except train/valid/test.jsonl), combines
them, deduplicates, shuffles, and splits 80/10/10.
"""

import json
import random
import hashlib
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SPLIT_FILES = {"train.jsonl", "valid.jsonl", "test.jsonl"}
SEED = 42


def load_jsonl(path: Path) -> list[dict]:
    """Load a JSONL file. Each line must have a 'messages' key."""
    examples = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "messages" in obj:
                    examples.append(obj)
                else:
                    print(f"  Warning: {path.name} line {i} missing 'messages' key, skipped")
            except json.JSONDecodeError as e:
                print(f"  Warning: {path.name} line {i} invalid JSON: {e}")
    return examples


def content_hash(example: dict) -> str:
    """Hash the user+assistant text to detect duplicates."""
    parts = []
    for msg in example.get("messages", []):
        parts.append(msg.get("role", "") + ":" + msg.get("content", ""))
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def main():
    # Find all JSONL source files (skip the output splits)
    source_files = sorted(
        p for p in DATA_DIR.glob("**/*.jsonl")
        if p.name not in SPLIT_FILES
    )

    if not source_files:
        print("No source JSONL files found in data/. Run seed_examples.py or prepare_data.py first.")
        return

    # Load and combine
    all_examples = []
    for path in source_files:
        examples = load_jsonl(path)
        print(f"  Loaded {len(examples):>5} examples from {path.relative_to(DATA_DIR)}")
        all_examples.extend(examples)

    print(f"\n  Total loaded: {len(all_examples)}")

    # Deduplicate
    seen = set()
    unique = []
    for ex in all_examples:
        h = content_hash(ex)
        if h not in seen:
            seen.add(h)
            unique.append(ex)

    dupes = len(all_examples) - len(unique)
    if dupes:
        print(f"  Removed {dupes} duplicates")
    all_examples = unique
    print(f"  Unique examples: {len(all_examples)}")

    # Shuffle
    rng = random.Random(SEED)
    rng.shuffle(all_examples)

    # Split 80/10/10
    n = len(all_examples)
    n_test = max(1, n // 10)
    n_valid = max(1, n // 10)

    test = all_examples[:n_test]
    valid = all_examples[n_test:n_test + n_valid]
    train = all_examples[n_test + n_valid:]

    # Write (mlx-lm format: only {"messages": [...]})
    for name, split in [("train.jsonl", train), ("valid.jsonl", valid), ("test.jsonl", test)]:
        path = DATA_DIR / name
        with open(path, "w", encoding="utf-8") as f:
            for ex in split:
                clean = {"messages": ex["messages"]}
                f.write(json.dumps(clean, ensure_ascii=False) + "\n")
        print(f"  Wrote {len(split):>5} → {name}")

    print(f"\nDone! Files in {DATA_DIR}")


if __name__ == "__main__":
    main()
