"""Minimal Coinbase Advanced Trade REST client.

Auth: HMAC SHA256 signature using API key + secret.

Environment:
- COINBASE_ADV_API_KEY
- COINBASE_ADV_API_SECRET

Notes:
- This implements the common pattern: signature = HMAC_SHA256(secret, timestamp + method + request_path + body)
  then base64-encoded.
- If your Coinbase key type uses a different auth scheme (e.g., JWT/CDP), tell me and I’ll adjust.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping

import requests


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


def load_config() -> CoinbaseAdvConfig:
    return CoinbaseAdvConfig(
        api_key=_require_env("COINBASE_ADV_API_KEY"),
        api_secret=_require_env("COINBASE_ADV_API_SECRET"),
    )


def _sign(secret: str, message: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


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
    ts = str(int(time.time()))

    # Coinbase-style signature payload
    message = f"{ts}{method_u}{request_path}{body}"
    sig = _sign(cfg.api_secret, message)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "CB-ACCESS-KEY": cfg.api_key,
        "CB-ACCESS-SIGN": sig,
        "CB-ACCESS-TIMESTAMP": ts,
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

    # Try to parse JSON either way for good error messages
    try:
        payload = r.json()
    except Exception:
        payload = {"raw": r.text}

    if r.status_code >= 400:
        raise CoinbaseAdvError(f"HTTP {r.status_code} calling {request_path}: {payload}")

    if not isinstance(payload, dict):
        return {"data": payload}
    return payload
