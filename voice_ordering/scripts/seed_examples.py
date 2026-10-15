"""Seed demo data without the Flask CLI.

    python scripts/seed_examples.py [--reset]

Prints the generated administrator password once (if a new account was created)
and the tracking tokens for the seeded requests, which you can paste into the
"मेरा अनुरोधहरू / My requests" page to try the tracking flow.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.seed import seed_demo_data  # noqa: E402


def main() -> int:
    reset = "--reset" in sys.argv
    app = create_app()
    with app.app_context():
        db.create_all()
        results = seed_demo_data(reset=reset)

    print("\n🌱 Demo data ready\n")
    for code, token, note in results:
        if code == "__admin_password__":
            print(f"   Administrator: {note} / {token}   ← change this after signing in")
        elif token:
            print(f"   {code}  tracking token: {token}   [{note}]")
        else:
            print(f"   {code}  [{note}]")
    print("\n   Voice page:  http://127.0.0.1:5001/")
    print("   Admin page:  http://127.0.0.1:5001/admin/\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
