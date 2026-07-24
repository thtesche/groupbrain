"""
Weekly digest generator for groupbrain.
Gathers tasks, decisions, and blockers, formats as markdown, posts to Telegram.
"""
import os
from datetime import datetime, timedelta
from pathlib import Path
from db import get_db


def generate_digest(days: int = 7) -> str:
    """Generate a weekly digest from the last N days."""
    conn = get_db()
    since = (datetime.now() - timedelta(days=days)).isoformat()

    # Open tasks
    tasks = conn.execute(
        "SELECT title, author, status, created_at FROM tasks WHERE created_at >= ? ORDER BY created_at DESC",
        (since,)
    ).fetchall()

    # Decisions
    decisions = conn.execute(
        "SELECT topic, decision, author, created_at FROM decisions WHERE created_at >= ? ORDER BY created_at DESC",
        (since,)
    ).fetchall()

    # Blockers
    blockers = conn.execute(
        "SELECT title, reporter, status, created_at FROM blockers WHERE created_at >= ? ORDER BY created_at DESC",
        (since,)
    ).fetchall()

    # Build digest
    lines = [f"📊 **Wochen-Recap** ({(datetime.now() - timedelta(days=days)).strftime('%d.%m.')} – {datetime.now().strftime('%d.%m.')})", ""]

    # Decisions section
    if decisions:
        lines.append("**✅ ENTSCHEIDUNGEN:**")
        for d in decisions:
            lines.append(f" - {d[1]} ({d[2]}, {d[3][:10]})")
        lines.append("")

    # Open tasks section
    open_tasks = [t for t in tasks if t[2] != "done"]
    if open_tasks:
        lines.append("**📌 OFFENE TASKS:**")
        for t in open_tasks:
            status_icon = {"open": "🟡", "in_progress": "🔧"}.get(t[2], "📋")
            lines.append(f" {status_icon} {t[0]} (@{t[1]})")
        lines.append("")

    # Done tasks (summary)
    done_tasks = [t for t in tasks if t[2] == "done"]
    if done_tasks:
        lines.append("**🎯 ABGESCHLOSSEN:**")
        for t in done_tasks:
            lines.append(f" ✅ {t[0]}")
        lines.append("")

    # Blockers
    active_blockers = [b for b in blockers if b[2] == "active"]
    if active_blockers:
        lines.append("**🚧 BLOCKER:**")
        for b in active_blockers:
            lines.append(f" 🔴 {b[0]} (gemeldet von @{b[1]})")
        lines.append("")

    # No activity
    if not tasks and not decisions and not blockers:
        lines.append("Keine Aktivitäten in den letzten {} Tagen.".format(days))

    return "\n".join(lines)


def save_digest(content: str, chat_id: str) -> None:
    """Save digest to database."""
    conn = get_db()
    conn.execute(
        "INSERT INTO digests (content, chat_id, posted_at) VALUES (?, ?, ?)",
        (content, chat_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
