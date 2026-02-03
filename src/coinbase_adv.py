"""Minimal Coinbase Advanced Trade REST client.

Auth: JWT (CDP API keys — Key ID + Private key).

Environment:
- COINBASE_ADV_API_KEY   = Key ID (e.g. organizations/{org_id}/apiKeys/{key_id} or the key ID alone)
- COINBASE_ADV_API_SECRET = Private key (PEM string; use \\n for newlines in .env)

Your "API key name", "Private key", and "Key ID" from Coinbase map as:
- Key ID       → COINBASE_ADV_API_KEY
- Private key  → COINBASE_ADV_API_SECRET (the PEM, with \\n for line breaks in .env)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping

import requests

# JWT auth for CDP keys (Key ID + Private key)
from coinbase import jwt_generator


@dataclass(frozen=True)
class CoinbaseAdvConfig:
    api_key: str
    api_secret: str
    base_url: str = "https://api.coinbase.com"


class CoinbaseAdvError(RuntimeError):
    pass


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise CoinbaseAdvError(f"Missing environment variable: {name}")
    return v


def _normalize_pem(secret: str) -> str:
    """Ensure PEM has real newlines so cryptography can parse it."""
    # .env may give literal backslash-n (two chars); turn into real newlines
    secret = secret.replace("\\n", "\n")
    # If PEM is still one long line (no newlines), fix framing for cryptography
    if "-----BEGIN " in secret and "\n" not in secret.strip():
        i = secret.find("-----BEGIN ")
        # End of BEGIN line is the next "-----" (closes "-----BEGIN ... -----")
        k = secret.find("-----", i + 11)
        if k == -1:
            return secret
        begin_line = secret[i : k + 5]
        rest = secret[k + 5 :]
        m = rest.find("-----END ")
        if m == -1:
            return secret
        base64_part = rest[:m].replace(" ", "").replace("\n", "")
        end_start = m
        end_close = rest.find("-----", end_start + 9)
        end_line = rest[end_start : end_close + 5] if end_close != -1 else rest[end_start:]
        secret = f"{begin_line}\n{base64_part}\n{end_line}\n"
    return secret


def load_config() -> CoinbaseAdvConfig:
    key = _require_env("COINBASE_ADV_API_KEY")
    secret = _require_env("COINBASE_ADV_API_SECRET")
    if "BEGIN " in secret or "PRIVATE KEY" in secret:
        secret = _normalize_pem(secret)
    return CoinbaseAdvConfig(api_key=key, api_secret=secret)


def request(
    cfg: CoinbaseAdvConfig,
    method: str,
    request_path: str,
    *,
    params: Mapping[str, Any] | None = None,
    json_body: Any | None = None,
    timeout_s: int = 30,
) -> dict[str, Any]:
    method_u = method.upper()
    body = "" if json_body is None else json.dumps(json_body, separators=(",", ":"))

    # Build JWT for this request (CDP keys: Key ID + Private key)
    jwt_uri = jwt_generator.format_jwt_uri(method_u, request_path)
    jwt = jwt_generator.build_rest_jwt(jwt_uri, cfg.api_key, cfg.api_secret)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt}",
    }

    url = cfg.base_url.rstrip("/") + request_path
    r = requests.request(
        method_u,
        url,
        headers=headers,
        params=dict(params) if params else None,
        data=body if body else None,
        timeout=timeout_s,
    )

    try:
        payload = r.json()
    except Exception:
        payload = {"raw": r.text}

    if r.status_code >= 400:
        raise CoinbaseAdvError(f"HTTP {r.status_code} calling {request_path}: {payload}")

    if not isinstance(payload, dict):
        return {"data": payload}
    return payload
