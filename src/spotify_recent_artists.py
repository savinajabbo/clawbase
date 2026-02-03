"""Print recently played artists (deduped) via Spotify Web API."""

from __future__ import annotations

from collections import Counter

from dotenv import load_dotenv

from .spotify_client import api_get


def main() -> int:
    load_dotenv()

    # limit max 50
    resp = api_get("/me/player/recently-played", params={"limit": 50})
    items = resp.get("items", [])

    artists: list[str] = []
    for it in items:
        track = (it or {}).get("track") or {}
        for a in track.get("artists", []) or []:
            name = a.get("name")
            if name:
                artists.append(name)

    counts = Counter(artists)
    for name, n in counts.most_common():
        print(f"{name} ({n})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
