#!/usr/bin/env python3
"""
GroupBrain — Telegram group knowledge extraction.
Passively observes messages, extracts tasks/decisions/blockers,
generates weekly digests.
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Start the GroupBrain bot."""
    print("🧠 GroupBrain starting...")
    print("   Listening to Telegram group for tasks, decisions, and blockers.")
    print("   Use /help in DM for commands.")
    print()

    # Import and run bot
    from bot import main
    main()


if __name__ == "__main__":
    main()
