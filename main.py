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
from telethon import TelegramClient

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

# ── Telegram send logic ──────────────────────────────────────────────

TELEGRAM_MAX_LENGTH = 4000


def split_digest(text: str, max_len: int = TELEGRAM_MAX_LENGTH) -> list[str]:
    """Split markdown digest into chunks that fit Telegram's 4096 limit."""
    chunks = []
    current = ""

    for paragraph in text.split("\n\n"):
        if current and len(current) + 2 + len(paragraph) > max_len:
            chunks.append(current)
            current = paragraph
        elif len(paragraph) > max_len:
            while len(paragraph) > max_len:
                split_at = paragraph.rfind(" ", 0, max_len)
                if split_at == -1:
                    split_at = max_len
                chunks.append(paragraph[:split_at])
                paragraph = paragraph[split_at:].lstrip()
            current = paragraph if paragraph else ""
        else:
            current = current + "\n\n" + paragraph if current else paragraph

    if current:
        chunks.append(current)

    return chunks


async def send_digest_to_telegram(digest_text: str, chat_id: str, api_id: str, api_hash: str) -> bool:
    """Send digest to Telegram group, splitting into chunks if necessary."""
    client = TelegramClient('groupbrain_session', int(api_id), api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("[!] ERROR: Session invalid. Run 'python telegram_auth_user.py'.")
            return False

        chunks = split_digest(digest_text)

        if len(chunks) > 1:
            print(f"[*] Digest split into {len(chunks)} message(s).")
        else:
            print("[*] Sending digest as single message...")

        for i, chunk in enumerate(chunks):
            prefix = f"*(Part {i+1}/{len(chunks)})* " if len(chunks) > 1 else ""
            await client.send_message(int(chat_id), prefix + chunk, parse_mode="markdown")
            print(f"  ✓ Sent: Part {i+1}/{len(chunks)} ({len(chunk)} chars)")

        print("[+] Digest sent successfully.")
        return True

    finally:
        await client.disconnect()


# ── Main orchestrator ────────────────────────────────────────────────

async def main():
    # Parse --days argument
    days = 7
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])

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

    # Step 3: Send to Telegram
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
