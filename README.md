# coinbase-api-test

Tiny Python sandbox for testing Coinbase APIs.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

Public (no auth) example:

```bash
python -m src.public_prices
```

## Notes

- This project includes a **public** example that does not require keys.
- If you want **authenticated** calls, tell me which Coinbase API you mean (Advanced Trade vs Coinbase API v2), and I’ll add the correct auth/signing flow.
