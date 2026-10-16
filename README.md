# Tech Support LLM

A fine-tuned language model for IT troubleshooting, built with Apple MLX on a Mac.

Trained on **1,002 curated Q&A examples** covering networking, Windows and Linux administration, cloud and DevOps, security, Microsoft 365, virtualization, helpdesk workflows, and more.

**Base model:** `mlx-community/Llama-3.2-3B-Instruct-4bit`  
**Method:** LoRA fine-tuning via `mlx-lm` on Apple Silicon  
**Dataset:** 802 train / 100 validation / 100 test examples  

## Quick start

You need a Mac with Apple Silicon (M-series) and Python 3.10+.

```bash
# Clone and set up
git clone https://github.com/ssvvikas/tech-support-llm.git
cd tech-support-llm
python3 -m venv venv
source venv/bin/activate
pip install mlx-lm

# Train (5–15 minutes on M1/M2/M3)
mlx_lm.lora \
  --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --train --data ./data --iters 1000

# Ask a question
mlx_lm.generate \
  --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --adapter-path adapters \
  --prompt "My laptop won't connect to Wi-Fi"
```

The first run downloads the base model (~2 GB). LoRA adapters are saved to `adapters/`.

## Example output

```
WiFi connection failures have several common causes. Let me walk you through
the troubleshooting steps:

1. Check if Wi-Fi is enabled, look for the physical switch or Fn key on your
   laptop, and check the WiFi icon in the system tray.
2. Forget and reconnect to the network: Settings → Network & Internet → Wi-Fi
   → Manage known networks → select the network → Forget, then reconnect.
3. Run the Windows network troubleshooter: Settings → Network & Internet →
   Status → Network troubleshooter.
4. Reset the network stack: open admin CMD and run 'netsh winsock reset',
   'netsh int ip reset', 'ipconfig /flushdns', then restart...
```

## What's in the training data

All 1,002 examples are hand written Q&A pairs in a clear, step-by-step troubleshooting style. Topics include:

- **Networking** : DNS, DHCP, VPN, VLANs, TCP/UDP, NAT, firewall rules, Wi-Fi troubleshooting, load balancers, SD-WAN, MPLS
- **Windows administration** :Active Directory, Group Policy, BSOD diagnosis, WSUS, BitLocker, RDP, PowerShell scripting, Windows Server hardening
- **Linux administration** : SSH key auth, disk management, file permissions, server hardening, iptables, systemd services
- **Cloud and DevOps** :Azure, AWS, Kubernetes, Docker, Terraform, CI/CD pipelines, IaC, containerization
- **Security** : Zero Trust, SIEM, EDR, MFA, ransomware response, phishing prevention, SSL/TLS certificates, WAF
- **Microsoft 365** : Exchange/Outlook, Teams, SharePoint, Conditional Access, shared mailboxes, license management
- **Virtualization** : VMware vSphere, Hyper-V, Type 1 vs Type 2 hypervisors, VM troubleshooting
- **Helpdesk and ITSM** : Ticket prioritization, ITIL processes, onboarding/offboarding, documentation, escalation procedures
- **Monitoring** : Prometheus/Grafana, ELK Stack, Zabbix, SNMP, Windows Performance Monitor, centralized logging
- **Hardware** : RAID levels, NAS setup, printer troubleshooting, laptop repair, data recovery, asset management
- **Backup and DR** : 3-2-1 rule, full/incremental/differential backups, disaster recovery planning, hot/warm/cold sites

## Training configuration

| Parameter | Value |
|-----------|-------|
| Base model | Llama-3.2-3B-Instruct (4-bit) |
| Fine-tuning method | LoRA |
| LoRA rank | 8 |
| LoRA layers | 16 |
| Learning rate | 1e-05 |
| Batch size | 4 |
| Iterations | 1000 |
| Max sequence length | 2048 |
| Optimizer | Adam |
| Trainable parameters | 0.216% |
| Checkpoints saved | Every 100 iterations |

## Project structure

```
tech-support-llm/
├── data/
│   ├── seed_examples.jsonl        # initial 101 examples
│   ├── all_examples.jsonl         # batches 1–10
│   ├── extra_examples_11–19.jsonl # batches 11–19
│   ├── train.jsonl                # training split (802 examples)
│   ├── valid.jsonl                # validation split (100 examples)
│   └── test.jsonl                 # test split (100 examples)
├── scripts/
│   ├── seed_examples.py           # generates the seed dataset
│   ├── extra_examples_11–19.py    # generate additional batches
│   ├── prepare_data.py            # fetches Stack Exchange data
│   └── build_splits.py            # combines all data, deduplicates, splits 80/10/10
├── adapters/                      # LoRA weights (created after training)
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Expanding the dataset

Add more examples by creating a new script in `scripts/`:

```python
#!/usr/bin/env python3
import json, pathlib

examples = [
    ("User's question here?", "Step-by-step answer here."),
    # ... more pairs
]

outpath = pathlib.Path(__file__).resolve().parent.parent / "data" / "my_examples.jsonl"
with open(outpath, "w") as f:
    for q, a in examples:
        record = {"messages": [
            {"role": "user", "content": q},
            {"role": "assistant", "content": a}
        ]}
        f.write(json.dumps(record) + "\n")
print(f"Wrote {len(examples)} examples to {outpath}")
```

Then rebuild the splits and retrain:

```bash
python scripts/my_examples.py       # generate JSONL
python scripts/build_splits.py      # rebuild train/valid/test (auto-deduplicates)
mlx_lm.lora --model mlx-community/Llama-3.2-3B-Instruct-4bit \
  --train --data ./data --iters 1000
```

## Requirements

- **Hardware:** Mac with Apple Silicon (M1 or later), 8 GB+ RAM
- **Software:** Python 3.10+, mlx-lm
- **Disk:** ~3 GB (base model download + adapters)
- **OS:** macOS 13 (Ventura) or later

> **Note:** MLX only works on Apple Silicon Macs. For Windows or Linux, check out
> [llama.cpp](https://github.com/ggerganov/llama.cpp) or
> [Hugging Face Transformers](https://github.com/huggingface/transformers).

## Roadmap

- [x] v0.1 — Initial model with seed data
- [x] v0.2 — Expand to 1,000+ curated examples, retrain
- [ ] v0.3 — Add RAG over public documentation
- [ ] v1.0 — Retrain on a stronger base model, publish to Hugging Face

## Contributing

Want to add training examples? See [CONTRIBUTING.md](CONTRIBUTING.md) for the format and guidelines.

## License

Code: MIT. Training data includes CC BY-SA 4.0 content from Stack Exchange.
