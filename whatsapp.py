"""
WhatsApp chat backup parser.
Exports messages from WhatsApp's SQLite database to our groupbrain database.
"""
import sqlite3
import os
import glob
from pathlib import Path
from datetime import datetime
from db import get_db


def find_whatsapp_databases() -> list[str]:
    """Find WhatsApp chat databases on macOS."""
    patterns = [
        str(Path.home() / "Library" / "Mobile Documents" / "com~apple~Messages" / "WhatsApp" / "*.db"),
        str(Path.home() / "Library" / "Application Support" / "WhatsApp" / "*.db"),
    ]
    found = []
    for pattern in patterns:
        found.extend(glob.glob(pattern))
    return found


def parse_database(db_path: str, source: str = "whatsapp") -> int:
    """Parse a WhatsApp database and import messages into groupbrain."""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return 0

    conn = sqlite3.connect(db_path)
    groupbrain = get_db()

    # Try common table names for WhatsApp messages
    tables = ["message", "messages", "wa_messages"]
    messages = []
    for table in tables:
        try:
            rows = conn.execute(f"SELECT * FROM {table} LIMIT 100").fetchall()
            if rows:
                columns = [desc[0] for desc in conn.execute(f"SELECT * FROM {table} LIMIT 1").description]
                messages = [(dict(zip(columns, row)) for row in conn.execute(f"SELECT * FROM {table}"))]
                break
        except sqlite3.OperationalError:
            continue

    conn.close()

    if not messages:
        print(f"No messages found in {db_path}")
        return 0

    # Map WhatsApp columns to our schema
    count = 0
    for row in messages:
        try:
            text = row.get("body", row.get("data", row.get("message", "")))
            timestamp = row.get("date", row.get("timestamp", datetime.now().isoformat()))
            sender = row.get("key_from_me", row.get("from_me", True))

            groupbrain.execute(
                "INSERT OR IGNORE INTO messages (timestamp, chat_id, user_name, source, text) VALUES (?, ?, ?, ?, ?)",
                (str(timestamp), "whatsapp", sender, source, str(text))
            )
            count += 1
        except (KeyError, TypeError):
            continue

    groupbrain.commit()
    groupbrain.close()
    print(f"Imported {count} messages from {db_path}")
    return count


def import_all() -> int:
    """Find and parse all WhatsApp databases."""
    total = 0
    for db_path in find_whatsapp_databases():
        total += parse_database(db_path)
    return total


if __name__ == "__main__":
    import_all()
