"""Minimal Spotify Web API client with token refresh.

Environment:
- SPOTIFY_CLIENT_ID
- SPOTIFY_REDIRECT_URI (must match the one in Spotify Developer Dashboard)

Token storage:
- Writes to .spotify-token.json in project root (gitignored).

Scopes used by scripts:
- user-read-recently-played
- user-follow-read

Docs: https://developer.spotify.com/documentation/web-api
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import requests


class SpotifyError(RuntimeError):
    pass


def _project_root() -> Path:
    # src/spotify_client.py -> project root
    return Path(__file__).resolve().parents[1]


TOKEN_PATH = _project_root() / ".spotify-token.json"


@dataclass
class SpotifyTokens:
    access_token: str
    token_type: str
    expires_at: int
    refresh_token: str | None = None
    scope: str | None = None

    @property
    def expired(self) -> bool:
        return int(time.time()) >= self.expires_at - 30


def load_tokens() -> SpotifyTokens:
    if not TOKEN_PATH.exists():
        raise SpotifyError(
            f"Missing {TOKEN_PATH.name}. Run: python -m src.spotify_login to authorize once."
        )
    data = json.loads(TOKEN_PATH.read_text())
    return SpotifyTokens(**data)


def save_tokens(tokens: SpotifyTokens) -> None:
    TOKEN_PATH.write_text(json.dumps(tokens.__dict__, indent=2, sort_keys=True))


def _env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise SpotifyError(f"Missing environment variable {name}")
    return v


def refresh_access_token(refresh_token: str) -> SpotifyTokens:
    client_id = _env("SPOTIFY_CLIENT_ID")

    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
        },
        timeout=30,
    )
    payload = r.json()
    if r.status_code >= 400:
        raise SpotifyError(f"Refresh failed: {payload}")

    expires_in = int(payload["expires_in"])
    return SpotifyTokens(
        access_token=payload["access_token"],
        token_type=payload.get("token_type", "Bearer"),
        expires_at=int(time.time()) + expires_in,
        refresh_token=payload.get("refresh_token") or refresh_token,
        scope=payload.get("scope"),
    )


def get_valid_tokens() -> SpotifyTokens:
    tokens = load_tokens()
    if tokens.expired:
        if not tokens.refresh_token:
            raise SpotifyError("Token expired and no refresh_token present. Re-run spotify_login.")
        tokens = refresh_access_token(tokens.refresh_token)
        save_tokens(tokens)
    return tokens


def api_get(path: str, *, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    tokens = get_valid_tokens()
    url = "https://api.spotify.com/v1" + path
    r = requests.get(
        url,
        headers={"Authorization": f"Bearer {tokens.access_token}"},
        params=dict(params) if params else None,
        timeout=30,
    )
    payload = r.json() if r.content else {}
    if r.status_code >= 400:
        raise SpotifyError(f"GET {path} failed ({r.status_code}): {payload}")
    if isinstance(payload, dict):
        return payload
    return {"data": payload}
