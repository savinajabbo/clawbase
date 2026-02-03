"""List accounts via Coinbase Advanced Trade API.

Requires:
- COINBASE_ADV_API_KEY
- COINBASE_ADV_API_SECRET

Run:
  python -m src.list_accounts
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

from .coinbase_adv import load_config, request


def main(argv: list[str]) -> int:
    load_dotenv()
    cfg = load_config()

    # Advanced Trade brokerage accounts endpoint
    resp = request(cfg, "GET", "/api/v3/brokerage/accounts")

    accounts = resp.get("accounts") or resp.get("data") or []
    if not accounts:
        print(resp)
        return 0

    # Print a compact view
    for a in accounts:
        name = a.get("name") or a.get("currency") or a.get("uuid")
        uuid = a.get("uuid") or a.get("id")
        avail = (a.get("available_balance") or {}).get("value") if isinstance(a.get("available_balance"), dict) else None
        cur = (a.get("available_balance") or {}).get("currency") if isinstance(a.get("available_balance"), dict) else None
        print(f"{name}  ({uuid})  available={avail} {cur}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
