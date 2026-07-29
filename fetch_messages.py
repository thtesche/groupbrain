#!/usr/bin/env python3
"""
GroupBrain — Fetch messages from Telegram and store in SQLite.
Uses read_messages.py to fetch real Telegram messages with full metadata.

Usage:
    python fetch_messages.py --limit 100 --offset 0  # Fetch messages from Telegram
    python fetch_messages.py --list                  # Show stored messages
"""
import os
import sys
import json
import asyncio
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from db import get_db
from read_messages import read_messages

load_dotenv(Path(__file__).parent / ".env")

GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")


async def fetch_messages_from_telegram(limit: int = 100, offset: int = 0) -> None:
    """Fetch messages from Telegram and store in DB with full metadata."""
    if not GROUP_CHAT_ID:
        print("ERROR: GROUP_CHAT_ID not set in .env")
        sys.exit(1)
    
    print(f"📩 Fetching messages from group: {GROUP_CHAT_ID}")
    print(f"   Limit: {limit}, Offset: {offset}\n")
    
    messages, username_map = await read_messages(limit=limit, offset=offset)
    
    print(f"  ✅ Fetched {len(messages)} message(s)\n")
    
    conn = get_db()
    
    # Create users table for username mapping
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            sender_id TEXT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Store username_map in users table
    for sid, display_name in username_map.items():
        # Parse "first_name @username" or just "first_name"
        parts = display_name.split()
        first_name = parts[0] if parts else None
        username = None
        for part in parts[1:]:
            if part.startswith("@"):
                username = part[1:]  # Remove @
                break
        
        conn.execute(
            "INSERT OR IGNORE INTO users (sender_id, username, first_name) VALUES (?, ?, ?)",
            (sid, username, first_name),
        )
    
    # Store messages with metadata
    for msg in messages:
        # Build metadata dict
        metadata = {}
        if "reactions" in msg:
            metadata["reactions"] = msg["reactions"]
        if "thread_id" in msg:
            metadata["thread_id"] = msg["thread_id"]
        if "is_forum_topic" in msg:
            metadata["is_forum_topic"] = msg["is_forum_topic"]
        if "reply_to_id" in msg:
            metadata["reply_to_id"] = msg["reply_to_id"]
        if "forwarded" in msg:
            metadata["forwarded"] = msg["forwarded"]
        if "forward_from" in msg:
            metadata["forward_from"] = msg["forward_from"]
        if "has_media" in msg:
            metadata["has_media"] = msg["has_media"]
        if "media_type" in msg:
            metadata["media_type"] = msg["media_type"]
        if "button_count" in msg:
            metadata["button_count"] = msg["button_count"]
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        # Get display name from username_map
        sender_id_str = str(msg["sender_id"])
        user_name = username_map.get(sender_id_str, "")
        
        # Use the actual Telegram message date as timestamp
        msg_date = msg.get("date")
        
        conn.execute(
            """INSERT INTO messages (chat_id, message_id, user_id, user_name, source, text, is_bot_reply, metadata, timestamp)
               VALUES (?, ?, ?, ?, 'telegram', ?, 0, ?, ?)
               ON CONFLICT(chat_id, message_id, source) DO UPDATE SET
                   user_name = excluded.user_name,
                   text = excluded.text,
                   metadata = excluded.metadata,
                   timestamp = excluded.timestamp""",
            (str(GROUP_CHAT_ID), msg["message_id"], sender_id_str, user_name, msg["text"], metadata_json, msg_date),
        )
    
    conn.commit()
    conn.close()
    
    print(f"  ✅ Stored {len(messages)} message(s) in database.\n")


def _sync_fetch_messages_from_telegram(limit: int = 100, offset: int = 0) -> None:
    """CLI wrapper: runs the async fetch in a new event loop."""
    asyncio.run(fetch_messages_from_telegram(limit=limit, offset=offset))


def fetch_messages_list() -> None:
    """Show all stored messages."""
    conn = get_db()
    rows = conn.execute(
        "SELECT message_id, user_name, text, timestamp FROM messages ORDER BY id DESC"
    ).fetchall()
    conn.close()
    
    if not rows:
        print("  No messages stored yet.\n")
        return
    
    print(f"\n  {'='*70}")
    print(f"  Stored Messages ({len(rows)} entries)")
    print(f"  {'='*70}\n")
    
    for row in rows:
        print(f"  [{row[3][:19]}]  @{row[1]}  (msg #{row[0]}):")
        for i in range(0, len(row[2]), 100):
            print(f"    {row[2][i:i+100]}")
        print()
    
    print(f"  {'='*70}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch messages from Telegram")
    parser.add_argument("--limit", type=int, default=100, help="Max messages to fetch (default: 100)")
    parser.add_argument("--offset", type=int, default=0, help="Message offset for pagination (default: 0)")
    parser.add_argument("--list", action="store_true", help="Show stored messages")
    args = parser.parse_args()
    
    if args.list:
        fetch_messages_list()
    else:
        _sync_fetch_messages_from_telegram(limit=args.limit, offset=args.offset)


if __name__ == "__main__":
    main()
