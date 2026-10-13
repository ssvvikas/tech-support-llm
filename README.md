# Tech Support LLM

A fine-tuned language model for IT troubleshooting, built with Apple MLX on a Mac.

## What is this?

A small open-source LLM trained on real tech support Q&A data. It learns a
clear, step-by-step troubleshooting style from public Stack Exchange answers
and hand-written examples.

**Base model:** `mlx-community/Llama-3.2-3B-Instruct-4bit`
**Fine-tuning:** LoRA via `mlx-lm` on Apple Silicon

## Download and run locally

You need a Mac with Apple Silicon (M1/M2/M3/M4) and Python 3.10+.

### Step 1: Clone the repo

```bash
git clone https://github.com/ssvvikas/tech-support-llm.git
cd tech-support-llm
```

### Step 2: Set up Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install mlx-lm
```

### Step 3: Train the model (takes 5–15 minutes)

The training data is included in `data/`. Run the fine-tuning:

```bash
mlx_lm.lora --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --train --data ./data --iters 1000
```

This downloads the base model (~2 GB) the first time and saves LoRA adapters
to the `adapters/` folder.

### Step 4: Ask it a question

```bash
mlx_lm.generate --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --adapter-path adapters \
  --prompt "My VPN keeps disconnecting"
```

### Example output

```
VPN disconnections usually have a few common causes. Let me walk you through
the troubleshooting steps:

1. Check your internet connection first — open a browser and load a page
   without VPN. If that fails, the problem is your network, not the VPN.
2. Try switching between Wi-Fi and ethernet...
```

## Want more training data?

Fetch additional examples from Stack Exchange (Super User + Server Fault):

```bash
python scripts/prepare_data.py    # fetch from Stack Exchange API
python scripts/build_splits.py    # rebuild train/valid/test splits
```

Then retrain with the bigger dataset using the same train command above.

## Requirements

- **Hardware:** Mac with Apple Silicon (M1 or later), 8 GB+ RAM
- **Software:** Python 3.10+, mlx-lm
- **Disk:** ~3 GB (base model download + adapters)
- **OS:** macOS 13 (Ventura) or later

> **Note:** MLX only works on Apple Silicon Macs. If you're on Windows or Linux,
> check out [llama.cpp](https://github.com/ggerganov/llama.cpp) or
> [Hugging Face Transformers](https://github.com/huggingface/transformers)
> for running similar models on other hardware.

## Results

| Version | Base Model | Examples | Test Loss | Notes |
|---------|-----------|----------|-----------|-------|
| v0.1    | Llama-3.2-3B-4bit | 46 | TBD | First version, seed data only |

## Data sources

- [Super User](https://superuser.com) (Stack Exchange, CC BY-SA 4.0)
- [Server Fault](https://serverfault.com) (Stack Exchange, CC BY-SA 4.0)
- Hand-written troubleshooting notes
- Contributor submissions (see [CONTRIBUTING.md](CONTRIBUTING.md))

## Project structure

```
tech-support-llm/
├── data/
│   ├── seed_examples.jsonl    # hand-written training examples
│   ├── train.jsonl            # training split (80%)
│   ├── valid.jsonl            # validation split (10%)
│   └── test.jsonl             # test split (10%)
├── scripts/
│   ├── seed_examples.py       # generates the seed dataset
│   ├── prepare_data.py        # fetches Stack Exchange data
│   └── build_splits.py        # combines and splits all data
├── adapters/                  # LoRA weights (created after training)
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Roadmap

- **v0.1** — 3B model, ~1,000 examples, runs on Mac
- **v0.2** — More contributor examples, better test scores
- **v0.3** — Add RAG over public documentation
- **v1.0** — Retrain on a stronger base model with full dataset

## Contributing

Want to add training examples? See [CONTRIBUTING.md](CONTRIBUTING.md) for
the format and rules. All contributions are reviewed before merging.

## License

Code: MIT. Training data includes CC BY-SA 4.0 content from Stack Exchange.
