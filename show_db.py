#!/usr/bin/env python3
"""
GroupBrain — Show database contents.
Displays all tables: messages, tasks, decisions, blockers, digests.

Usage:
    python show_db.py                    # Show all tables
    python show_db.py --tasks            # Show only tasks
    python show_db.py --decisions        # Show only decisions
    python show_db.py --blockers         # Show only blockers
    python show_db.py --messages         # Show only messages
    python show_db.py --digests          # Show only digests
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import get_db


def show_messages(conn) -> None:
    rows = conn.execute(
        "SELECT message_id, user_name, text, timestamp, metadata FROM messages ORDER BY id DESC"
    ).fetchall()

    print(f"\n  📩 MESSAGES ({len(rows)} entries):")
    if not rows:
        print("    (none)\n")
        return

    for row in rows:
        print(f"    [{row[3][:19]}] @{row[1]} (msg #{row[0]}):")
        for i in range(0, len(row[2]), 100):
            print(f"      {row[2][i:i+100]}")
        
        # Show metadata annotations
        metadata = None
        if row[4]:
            try:
                import json
                metadata = json.loads(row[4])
            except (json.JSONDecodeError, TypeError):
                pass
        
        if metadata:
            annotations = []
            if metadata.get("reactions"):
                reaction_str = ", ".join(metadata["reactions"])
                annotations.append(f"reactions=[{reaction_str}]")
            if metadata.get("reply_to_id"):
                annotations.append(f"reply_to={metadata['reply_to_id']}")
            if metadata.get("thread_id"):
                ft = "forum-topic" if metadata.get("is_forum_topic") else "thread"
                annotations.append(f"thread={metadata['thread_id']} ({ft})")
            if metadata.get("forwarded"):
                annotations.append("forwarded")
            if metadata.get("has_media"):
                annotations.append(f"media={metadata.get('media_type', 'media')}")
            if metadata.get("button_count"):
                annotations.append(f"buttons={metadata['button_count']}")
            
            if annotations:
                print(f"      → {' '.join(annotations)}")
        
        print()


def show_tasks(conn) -> None:
    rows = conn.execute(
        "SELECT title, author, status, created_at, notes FROM tasks ORDER BY created_at DESC"
    ).fetchall()

    print(f"\n  📌 TASKS ({len(rows)} entries):")
    if not rows:
        print("    (none)\n")
        return

    for row in rows:
        status_icon = {"open": "🟡", "in_progress": "🔧", "done": "✅", "cancelled": "❌"}.get(row[2], "📋")
        author_str = f" (@{row[1]})" if row[1] else ""
        print(f"    {status_icon} {row[0]}{author_str} — {row[3][:10]}")
        if row[4]:
            print(f"      Note: {row[4]}")
    print()


def show_decisions(conn) -> None:
    rows = conn.execute(
        "SELECT topic, decision, author, created_at, rationale FROM decisions ORDER BY created_at DESC"
    ).fetchall()

    print(f"\n  ✅ DECISIONS ({len(rows)} entries):")
    if not rows:
        print("    (none)\n")
        return

    for row in rows:
        author_str = f" (@{row[2]})" if row[2] else ""
        print(f"    - **{row[0]}**: {row[1]}{author_str}")
        if row[4]:
            print(f"      Reason: {row[4]}")
    print()


def show_blockers(conn) -> None:
    rows = conn.execute(
        "SELECT title, reporter, status, created_at FROM blockers ORDER BY created_at DESC"
    ).fetchall()

    print(f"\n  🚧 BLOCKERS ({len(rows)} entries):")
    if not rows:
        print("    (none)\n")
        return

    for row in rows:
        status_icon = {"active": "🔴", "resolved": "🟢"}.get(row[2], "⚪")
        reporter_str = f" (@{row[1]})" if row[1] else ""
        print(f"    {status_icon} {row[0]}{reporter_str} — {row[3][:10]}")
    print()


def show_digests(conn) -> None:
    rows = conn.execute(
        "SELECT content, posted_at, chat_id FROM digests ORDER BY id DESC"
    ).fetchall()

    print(f"\n  📊 DIGESTS ({len(rows)} entries):")
    if not rows:
        print("    (none)\n")
        return

    for row in rows:
        print(f"    [{row[1][:19]}] (chat: {row[2]}):")
        for line in row[0].split("\n"):
            print(f"      {line}")
        print()


def show_all() -> None:
    conn = get_db()
    print(f"\n  {'='*70}")
    print(f"  GroupBrain Database")
    print(f"  {'='*70}")

    show_messages(conn)
    show_tasks(conn)
    show_decisions(conn)
    show_blockers(conn)
    show_digests(conn)

    print(f"  {'='*70}\n")
    conn.close()


def main() -> None:
    if len(sys.argv) > 1:
        flag = sys.argv[1]
        conn = get_db()
        print(f"\n  {'='*70}")
        print(f"  GroupBrain Database")
        print(f"  {'='*70}")

        if flag == "--messages":
            show_messages(conn)
        elif flag == "--tasks":
            show_tasks(conn)
        elif flag == "--decisions":
            show_decisions(conn)
        elif flag == "--blockers":
            show_blockers(conn)
        elif flag == "--digests":
            show_digests(conn)
        else:
            print(f"  Unknown flag: {flag}")
            conn.close()
            return

        print(f"  {'='*70}\n")
        conn.close()
    else:
        show_all()


if __name__ == "__main__":
    main()
