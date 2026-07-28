#!/usr/bin/env python3
"""
GroupBrain — Knowledge extraction from Telegram group chats.
Fetches messages with full metadata (reactions, threads, replies).
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Show usage instructions."""
    print("🧠 GroupBrain — Telegram Knowledge Extraction")
    print()
    print("Available tools:")
    print("  python fetch_messages.py --limit 100    # Fetch messages from Telegram")
    print("  python show_db.py [--messages]          # View database content")
    print("  python generate_digest_cli.py [--days]  # Generate weekly recap")
    print()
    print("Optional: Telegram authentication (one-time)")
    print("  python telegram_auth_user.py            # Create session file")
    print()


if __name__ == "__main__":
    main()
