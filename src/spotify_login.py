"""One-time Spotify login to obtain refresh token (PKCE).

Steps:
1) Create a Spotify Developer app and set redirect URI (e.g. http://127.0.0.1:8080/callback)
2) Put SPOTIFY_CLIENT_ID and SPOTIFY_REDIRECT_URI in .env
3) Run: python -m src.spotify_login

This starts a tiny local server to receive the OAuth callback.
"""

from __future__ import annotations

import os
import threading
import time
import webbrowser
from dataclasses import dataclass
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, request

from .spotify_client import SpotifyError, SpotifyTokens, save_tokens
from .spotify_pkce import code_challenge_s256, generate_code_verifier, generate_state


load_dotenv()

app = Flask(__name__)


@dataclass
class Session:
    code_verifier: str
    state: str
    client_id: str
    redirect_uri: str


SESSION: Session | None = None
DONE: dict[str, Any] = {}


@app.get("/callback")
def callback():
    global DONE
    if SESSION is None:
        return ("No session", 400)

    err = request.args.get("error")
    if err:
        DONE = {"error": err}
        return (f"Spotify auth error: {err}", 400)

    state = request.args.get("state")
    if state != SESSION.state:
        DONE = {"error": "state_mismatch"}
        return ("State mismatch", 400)

    code = request.args.get("code")
    if not code:
        DONE = {"error": "missing_code"}
        return ("Missing code", 400)

    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SESSION.redirect_uri,
            "client_id": SESSION.client_id,
            "code_verifier": SESSION.code_verifier,
        },
        timeout=30,
    )
    payload = r.json()
    if r.status_code >= 400:
        DONE = {"error": payload}
        return (f"Token exchange failed: {payload}", 400)

    expires_in = int(payload["expires_in"])
    tokens = SpotifyTokens(
        access_token=payload["access_token"],
        token_type=payload.get("token_type", "Bearer"),
        expires_at=int(time.time()) + expires_in,
        refresh_token=payload.get("refresh_token"),
        scope=payload.get("scope"),
    )
    save_tokens(tokens)
    DONE = {"ok": True, "scope": tokens.scope}
    return "Authorized. You can close this tab and return to the terminal."


def _env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise SpotifyError(f"Missing environment variable {name}")
    return v


def main() -> int:
    global SESSION

    client_id = _env("SPOTIFY_CLIENT_ID")
    redirect_uri = _env("SPOTIFY_REDIRECT_URI")

    code_verifier = generate_code_verifier()
    challenge = code_challenge_s256(code_verifier)
    state = generate_state()

    SESSION = Session(
        code_verifier=code_verifier,
        state=state,
        client_id=client_id,
        redirect_uri=redirect_uri,
    )

    scopes = [
        "user-read-recently-played",
        "user-follow-read",
    ]

    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={requests.utils.quote(redirect_uri, safe='')}"
        f"&scope={requests.utils.quote(' '.join(scopes), safe='')}"
        f"&state={state}"
        f"&code_challenge_method=S256"
        f"&code_challenge={challenge}"
    )

    # Run server in background
    host = "127.0.0.1"
    port = 8080

    def run_server():
        app.run(host=host, port=port, debug=False)

    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    print("Opening browser for Spotify authorization...")
    print(auth_url)
    webbrowser.open(auth_url)

    # Wait for callback
    for _ in range(600):  # ~60s
        if DONE:
            break
        time.sleep(0.1)

    if not DONE:
        raise SpotifyError("Timed out waiting for OAuth callback.")
    if DONE.get("ok") is True:
        print(f"Saved tokens. Scope={DONE.get('scope')}")
        return 0

    raise SpotifyError(f"Auth failed: {DONE.get('error')}")


if __name__ == "__main__":
    raise SystemExit(main())
