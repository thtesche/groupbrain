"""
Weekly digest generator for groupbrain.
Reads messages from SQLite, extracts via LLM, formats as markdown, posts to Telegram.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from db import get_db
from extract import extract_from_messages


def generate_digest(days: int = 7) -> str:
    """Generate a weekly digest from the last N days."""
    conn = get_db()

    rows = conn.execute(
        "SELECT id, message_id, user_name, text, chat_id, metadata FROM messages "
        "WHERE timestamp >= ? AND text NOT LIKE '📊 **Weekly Recap** %' "
        "ORDER BY id DESC LIMIT ?",
        ((datetime.now() - timedelta(days=days)).isoformat(), 1000),
    ).fetchall()
    conn.close()

    if not rows:
        return f"📊 **Weekly Recap** ({(datetime.now() - timedelta(days=days)).strftime('%m.%d.')} – {datetime.now().strftime('%m.%d.')})\n\nNo messages in the last {days} days."

    # Convert to dict format for extract_from_messages
    messages = []
    for row in rows:
        msg_dict = {
            "message_id": row[0],
            "telegram_message_id": row[1],
            "user_name": row[2],
            "text": row[3],
            "chat_id": row[4],
        }
        if row[5]:
            try:
                msg_dict["metadata"] = json.loads(row[5])
            except (json.JSONDecodeError, TypeError):
                msg_dict["metadata"] = None
        else:
            msg_dict["metadata"] = None
        messages.append(msg_dict)

    results = extract_from_messages(messages)
    if not results:
        return f"📊 **Weekly Recap** ({(datetime.now() - timedelta(days=days)).strftime('%m.%d.')} – {datetime.now().strftime('%m.%d.')})\n\nNo extraction results (check LLM configuration)."

    result = results[0]

    # Build digest
    lines = [f"📊 **Weekly Recap** ({(datetime.now() - timedelta(days=days)).strftime('%m.%d.')} – {datetime.now().strftime('%m.%d.')})", ""]

    # Decisions section
    if result.decisions:
        lines.append("**✅ DECISIONS:**")
        for d in result.decisions:
            author_str = f" (@{d.author})" if d.author else ""
            line = f" - {d.topic}: {d.decision}{author_str}"
            if d.rationale:
                line += f"\n    Reason: {d.rationale}"
            lines.append(line)
        lines.append("")

    # Tasks section - split into active and completed
    if result.tasks:
        active = [t for t in result.tasks if not (t.notes and ("erledigt" in t.notes.lower() or "completed" in t.notes.lower() or "done" in t.notes.lower() or "fertig" in t.notes.lower()))]
        completed = [t for t in result.tasks if t.notes and ("erledigt" in t.notes.lower() or "completed" in t.notes.lower() or "done" in t.notes.lower() or "fertig" in t.notes.lower())]

        if active:
            lines.append("**📌 TASKS:**")
            for t in active:
                author_str = f" (@{t.author})" if t.author else ""
                line = f" - {t.title}{author_str}"
                if t.notes:
                    line += f"\n    Note: {t.notes}"
                lines.append(line)
            lines.append("")

        if completed:
            lines.append("**✅ COMPLETED TASKS:**")
            for t in completed:
                author_str = f" (@{t.author})" if t.author else ""
                line = f" - {t.title}{author_str}"
                if t.notes:
                    line += f"\n    Note: {t.notes}"
                lines.append(line)
            lines.append("")

    # Blockers
    if result.blockers:
        lines.append("**🚧 BLOCKERS:**")
        for b in result.blockers:
            reporter_str = f" (reported by @{b.reporter})" if b.reporter else ""
            lines.append(f" - {b.title}{reporter_str}")
        lines.append("")

    # No activity
    if not result.tasks and not result.decisions and not result.blockers:
        lines.append(f"No activity in the last {days} days.")

    return "\n".join(lines)

