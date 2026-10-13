# Contributing

Thanks for helping improve the tech support training data!

## How to add examples

1. Fork this repo.
2. Add your examples to `data/contributed/` as a `.jsonl` file named after yourself
   (e.g., `data/contributed/your-github-name.jsonl`).
3. Each line must follow this format:

```json
{"messages": [{"role": "user", "content": "The question or problem"}, {"role": "assistant", "content": "Step-by-step answer"}]}
```

4. Open a pull request.

## Rules

- **NO company data.** No ticket numbers, customer names, internal system names, or IP addresses.
- **NO personal information.** No real names, emails, or identifying details.
- Write answers in clear, step-by-step style.
- One problem per example.
- Include the error message or symptom in the question when possible.
- Answers should explain *why* each step works, not just what to click.

## What makes a good example?

- Real problems you've solved (rewritten from memory, not copied from tickets).
- Common issues: VPN, printers, password resets, Wi-Fi, email, permissions, etc.
- Include the OS or environment when it matters (e.g., "on Windows 11").
- Warnings for anything risky (e.g., "This will delete all data on the drive").

## Review process

I review every PR before merging to check quality and make sure no private
info slipped in.
