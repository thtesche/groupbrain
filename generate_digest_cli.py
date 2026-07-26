#!/usr/bin/env python3
"""
GroupBrain — Generate and display weekly digest.
Reads from SQLite and formats a markdown recap.

Usage:
    python generate_digest_cli.py              # Last 7 days
    python generate_digest_cli.py --days 14    # Last 14 days
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from digest import generate_digest


def main() -> None:
    days = 7
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])

    content = generate_digest(days)

    print(f"\n  {'='*70}")
    print(f"  Wochen-Recap (letzte {days} Tage)")
    print(f"  {'='*70}")
    print()
    print(content)
    print()
    print(f"  {'='*70}\n")


if __name__ == "__main__":
    main()
