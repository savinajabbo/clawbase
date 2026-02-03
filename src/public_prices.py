"""Public Coinbase price fetch (no auth).

Uses Coinbase API v2 public endpoint.
Docs: https://developers.coinbase.com/api/v2
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import requests
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Price:
    base: str
    currency: str
    amount: str


def get_spot_price(base: str = "BTC", currency: str = "USD") -> Price:
    url = f"https://api.coinbase.com/v2/prices/{base}-{currency}/spot"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()["data"]
    return Price(base=data["base"], currency=data["currency"], amount=data["amount"])


def main(argv: list[str]) -> int:
    base = os.getenv("BASE", "BTC")
    currency = os.getenv("CURRENCY", "USD")
    p = get_spot_price(base=base, currency=currency)
    print(f"{p.base}-{p.currency}: {p.amount}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
