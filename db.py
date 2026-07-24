"""
SQLite storage for groupbrain tasks, decisions, and blockers.
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", str(Path.home() / ".hermes" / "data" / "groupbrain.db"))


def get_db() -> sqlite3.Connection:
    """Get a database connection, creating tables if needed."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _init_tables(conn)
    return conn


def _init_tables(conn: sqlite3.Connection) -> None:
    """Create all tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            chat_id TEXT NOT NULL,
            message_id INTEGER NOT NULL,
            user_id TEXT,
            user_name TEXT,
            source TEXT DEFAULT 'telegram',
            text TEXT NOT NULL,
            is_bot_reply INTEGER DEFAULT 0,
            UNIQUE(chat_id, message_id, source)
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'open',  -- open | in_progress | done | cancelled
            author TEXT,
            source_message_id INTEGER,
            source_chat_id TEXT,
            source TEXT DEFAULT 'telegram',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (source_message_id) REFERENCES messages
        );

        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            decision TEXT NOT NULL,
            rationale TEXT,
            author TEXT,
            source_message_id INTEGER,
            source_chat_id TEXT,
            source TEXT DEFAULT 'telegram',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS blockers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            status TEXT DEFAULT 'active',  -- active | resolved
            reporter TEXT,
            source_message_id INTEGER,
            source_chat_id TEXT,
            source TEXT DEFAULT 'telegram',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            chat_id TEXT
        );

        -- FTS5 for full-text search
        CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
            text, user_name, source, chat_id,
            content='messages',
            content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
            INSERT INTO messages_fts(rowid, text, user_name, source, chat_id)
            VALUES (new.id, new.text, new.user_name, new.source, new.chat_id);
        END;

        CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
            INSERT INTO messages_fts(messages_fts, rowid, text, user_name, source, chat_id)
            VALUES ('delete', old.id, old.text, old.user_name, old.source, old.chat_id);
        END;
    """)
    conn.commit()
