#!/usr/bin/env python3
"""
GroupBrain — Extract tasks, decisions, and blockers from stored messages.
Reads messages from SQLite, sends to LLM, displays results.

Usage:
    python extract_messages.py              # Process last 20 messages
    python extract_messages.py --limit 50   # Process last 50 messages
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import get_db
from extract import extract_from_messages


def extract_from_db(limit: int = 20) -> None:
    """Read messages from DB, extract via LLM, display results."""
    conn = get_db()

    rows = conn.execute(
        "SELECT id, message_id, user_name, text, chat_id, metadata FROM messages "
        "ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()

    if not rows:
        print("  No messages in database. Run fetch_messages.py first.\n")
        return

    # Convert to dict format for extract_from_messages
    # Use row[0] (AUTOINCREMENT PK) as message_id because FK source_message_id
    # references messages.id (AUTOINCREMENT PK), not messages.message_id.
    messages = []
    for row in rows:
        msg_dict = {
            "message_id": row[0],  # AUTOINCREMENT PK (for FK references)
            "telegram_message_id": row[1],  # Telegram message_id (for display)
            "user_name": row[2],
            "text": row[3],
            "chat_id": row[4],
        }
        # Parse metadata JSON if present
        if row[5]:
            try:
                msg_dict["metadata"] = json.loads(row[5])
            except (json.JSONDecodeError, TypeError):
                msg_dict["metadata"] = None
        else:
            msg_dict["metadata"] = None
        messages.append(msg_dict)

    print(f"  📩 Processing {len(messages)} message(s) from database...\n")

    results = extract_from_messages(messages)

    if not results:
        print("  ⚠️  No extraction results (check LLM configuration).\n")
        return

    result = results[0]

    print(f"  {'='*70}")
    print(f"  Extraction Results")
    print(f"  {'='*70}\n")

    if result.tasks:
        print(f"  📌 TASKS ({len(result.tasks)}):")
        for t in result.tasks:
            author_str = f" (@{t.author})" if t.author else ""
            completed_marker = " ✅ ERLEDIGT" if t.notes and ("erledigt" in t.notes.lower() or "completed" in t.notes.lower()) else ""
            print(f"    - {t.title}{author_str}{completed_marker}")
            if t.notes:
                print(f"      Note: {t.notes}")
        print()

    if result.decisions:
        print(f"  ✅ DECISIONS ({len(result.decisions)}):")
        for d in result.decisions:
            author_str = f" (@{d.author})" if d.author else ""
            print(f"    - **{d.topic}**: {d.decision}{author_str}")
            if d.rationale:
                print(f"      Reason: {d.rationale}")
        print()

    if result.blockers:
        print(f"  🚧 BLOCKERS ({len(result.blockers)}):")
        for b in result.blockers:
            reporter_str = f" (@{b.reporter})" if b.reporter else ""
            print(f"    - {b.title}{reporter_str}")
        print()


def main() -> None:
    limit = 20
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    extract_from_db(limit)


if __name__ == "__main__":
    main()
