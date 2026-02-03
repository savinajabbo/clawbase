# clawbase

Python sandbox for testing Coinbase + Spotify APIs.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Coinbase

Public (no auth) example:

```bash
python -m src.public_prices
```

List accounts (Advanced Trade, requires API keys in `.env`):

```bash
python -m src.list_accounts
```

## Spotify

One-time OAuth login (then tokens refresh automatically):

```bash
python -m src.spotify_login
```

Recently played artists:

```bash
python -m src.spotify_recent_artists
```

New releases from followed artists (heuristic):

```bash
python -m src.spotify_followed_new_releases
```

## Notes

- Coinbase Advanced Trade uses **CDP keys**: set **Key ID** as `COINBASE_ADV_API_KEY` and **Private key** (PEM) as `COINBASE_ADV_API_SECRET`. In `.env`, use `\n` for newlines in the PEM.
- Spotify uses the official Web API + OAuth PKCE. You still need to create a free Spotify Developer app (client id) once.
