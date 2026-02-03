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

List accounts (Advanced Trade, requires API keys in `.env`):

```bash
python -m src.list_accounts
```

## Notes

- This project includes a **public** example that does not require keys.
- Advanced Trade auth requires an API key + secret in `.env`.
