"""Spotify OAuth PKCE helpers."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def generate_code_verifier(length: int = 64) -> str:
    # Spotify: 43-128 chars; unreserved characters
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def code_challenge_s256(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    return _b64url(digest)


def generate_state(length: int = 32) -> str:
    return _b64url(os.urandom(length))
