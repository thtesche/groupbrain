#!/usr/bin/env python3
"""
GroupBrain — Weekly cron orchestrator.
Fetches messages, generates digest, sends it to Telegram.

Usage (cron):
    python main.py
    python main.py --days 14
"""
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# ── .env loading ───────────────────────────────────────────────────────

def load_env(filepath):
    """Load .env file manually."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        print(f"[!] Warning: .env file not found at {filepath}")

# ── Core imports (reuse existing modules) ──────────────────────────────

sys.path.insert(0, str(Path(__file__).parent))
from fetch_messages import fetch_messages_from_telegram
from digest import generate_digest
from telegram_client import send_digest_to_telegram, check_session_health

# ── Main orchestrator ────────────────────────────────────────────────

async def main():
    # Parse --days and --silent (dry-run) arguments
    days = 7
    silent = False
    args = sys.argv[1:]
    if "--silent" in args:
        silent = True
    if "--days" in args:
        idx = args.index("--days")
        if idx + 1 < len(args):
            days = int(args[idx + 1])

    # Load .env
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_env(env_path)

    # Configuration
    GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
    TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")

    if not all([GROUP_CHAT_ID, TELEGRAM_API_ID, TELEGRAM_API_HASH]):
        print("[!] ERROR: TELEGRAM_API_ID, TELEGRAM_API_HASH, GROUP_CHAT_ID missing in .env")
        sys.exit(1)

    print("=" * 60)
    print("  GroupBrain Weekly Digest")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Step 0: Health check - validate Telegram session before running pipeline
    print("\n[*] Step 0: Checking Telegram session health...")
    try:
        is_valid, message = await check_session_health(TELEGRAM_API_ID, TELEGRAM_API_HASH)
        if not is_valid:
            print(f"[!] Session check failed: {message}")
            print("[!] Skipping digest — Telegram delivery not possible.")
            sys.exit(1)
        print(f"  ✓ {message}")
    except Exception as e:
        print(f"[!] Unexpected error during session check: {e}")
        sys.exit(1)

    # Step 1: Fetch messages
    print("\n[*] Step 1: Fetching messages...")
    try:
        await fetch_messages_from_telegram(limit=100, offset=0)
    except Exception as e:
        print(f"[!] Error fetching messages: {e}")
        sys.exit(1)

    # Step 2: Generate digest
    print("\n[*] Step 2: Generating digest...")
    try:
        digest_text = generate_digest(days=days)
    except Exception as e:
        print(f"[!] Error generating digest: {e}")
        sys.exit(1)

    # Check if there's any content worth sending
    if "No messages" in digest_text or "No activity" in digest_text:
        print("[!] No new activity — digest skipped.")
        return

    # Validate digest has actual content (not just header)
    if digest_text.strip().startswith("📊 **Weekly Recap**") and len(digest_text.split("\n")) <= 2:
        print("[!] Digest contains no meaningful content — skipped.")
        return

    # Handle LLM extraction failure
    if "No extraction results" in digest_text:
        print("[!] LLM extraction returned no results — check LLM configuration.")
        if silent:
            print("\n" + "=" * 60)
            print("  DIGEST (would be sent to Telegram):")
            print("=" * 60)
            print(digest_text)
            print("=" * 60)
            print("  ✓ Weekly Digest completed (dry-run)")
            print("=" * 60)
        return

    # Step 3: Send to Telegram
    if silent:
        print("\n[*] Step 3: Silent mode — skipping Telegram delivery.")
        print("\n" + "=" * 60)
        print("  DIGEST (would be sent to Telegram):")
        print("=" * 60)
        print(digest_text)
        print("=" * 60)
        print("  ✓ Weekly Digest completed (dry-run)")
        print("=" * 60)
    else:
        print("\n[*] Step 3: Sending digest to Telegram...")
        try:
            success = await send_digest_to_telegram(
                digest_text=digest_text,
                chat_id=GROUP_CHAT_ID,
                api_id=TELEGRAM_API_ID,
                api_hash=TELEGRAM_API_HASH
            )
            if not success:
                print("[!] Telegram delivery failed.")
                sys.exit(1)
        except Exception as e:
            print(f"[!] Error sending digest: {e}")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("  ✓ Weekly Digest completed")
        print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
