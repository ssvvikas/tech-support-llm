# Tech Support LLM

A fine-tuned language model for IT troubleshooting, built with Apple MLX on a Mac.

## What is this?

A small open-source LLM trained on real tech support Q&A data. It learns a
clear, step-by-step troubleshooting style from public Stack Exchange answers
and hand-written examples.

**Base model:** `mlx-community/Llama-3.2-3B-Instruct-4bit`
**Fine-tuning:** LoRA via `mlx-lm` on Apple Silicon

## Quick start

```bash
pip install mlx-lm

# Train
mlx_lm.lora --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --train --data ./data --iters 1000

# Try it
mlx_lm.generate --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --adapter-path adapters \
  --prompt "My VPN keeps disconnecting"
```

## Results

| Version | Base Model | Examples | Test Loss | Notes |
|---------|-----------|----------|-----------|-------|
| v0.1    | Llama-3.2-3B-4bit | TBD | TBD | First version |

## Data sources

- [Super User](https://superuser.com) (Stack Exchange, CC BY-SA 4.0)
- [Server Fault](https://serverfault.com) (Stack Exchange, CC BY-SA 4.0)
- Hand-written troubleshooting notes
- Contributor submissions (see [CONTRIBUTING.md](CONTRIBUTING.md))

## Roadmap

- **v0.1** — 3B model, ~1,000 examples, runs on Mac
- **v0.2** — More contributor examples, better test scores
- **v0.3** — Add RAG over public documentation
- **v1.0** — Retrain on a stronger base model with full dataset

## License

Code: MIT. Training data includes CC BY-SA 4.0 content from Stack Exchange.
