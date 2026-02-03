"""Find new releases from followed artists.

Approach:
- Fetch followed artists: GET /me/following?type=artist (paged)
- Fetch new releases: GET /browse/new-releases (paged)
- Match albums' artists against your followed set.

This is a heuristic (Spotify doesn't provide a direct 'new releases from followed artists' endpoint).
"""

from __future__ import annotations

from datetime import datetime, timezone

from dotenv import load_dotenv

from .spotify_client import api_get


def iter_followed_artists_ids() -> set[str]:
    ids: set[str] = set()
    after = None

    while True:
        params = {"type": "artist", "limit": 50}
        if after:
            params["after"] = after
        resp = api_get("/me/following", params=params)
        artists = (resp.get("artists") or {})
        for a in artists.get("items", []) or []:
            if a.get("id"):
                ids.add(a["id"])
        after = artists.get("cursors", {}).get("after")
        if not after:
            break

    return ids


def iter_new_releases(limit_pages: int = 5) -> list[dict]:
    out: list[dict] = []
    offset = 0
    for _ in range(limit_pages):
        resp = api_get("/browse/new-releases", params={"limit": 50, "offset": offset})
        albums = (resp.get("albums") or {})
        out.extend(albums.get("items", []) or [])
        if not albums.get("next"):
            break
        offset += int(albums.get("limit") or 50)
    return out


def main() -> int:
    load_dotenv()

    followed = iter_followed_artists_ids()
    albums = iter_new_releases(limit_pages=6)

    matches = []
    for al in albums:
        artist_ids = {a.get("id") for a in (al.get("artists") or []) if a.get("id")}
        if artist_ids & followed:
            matches.append(al)

    # Sort newest-ish by release_date (string; not always full date)
    def key(alb: dict) -> str:
        return alb.get("release_date") or ""

    matches.sort(key=key, reverse=True)

    print(f"Matched {len(matches)} new releases from followed artists (heuristic).")
    now = datetime.now(timezone.utc).isoformat()
    print(f"Generated at {now}")

    for al in matches[:50]:
        name = al.get("name")
        artists = ", ".join(a.get("name", "") for a in (al.get("artists") or []))
        date = al.get("release_date")
        url = (al.get("external_urls") or {}).get("spotify")
        print(f"- {date} — {name} — {artists}\n  {url}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
