# groupbrain

## Purpose
Passive knowledge extraction from Telegram group chats. Uses Telethon to fetch real messages with full metadata (reactions, threads, replies), extracts tasks/decisions/blockers via LLM, and generates weekly digests.

## Architecture
```
Telegram Group ←── read_messages.py (Telethon)
                    ├── fetch_messages.py (SQLite storage)
                    ├── extract_messages.py (LLM extraction)
                    ├── show_db.py (SQLite Viewer)
                    └── generate_digest_cli.py (Weekly Digest)
```

## Quick Start
```bash
cd ~/.hermes/plugins/groupbrain
source venv/bin/activate

# 1. Fetch messages from Telegram (with metadata)
python fetch_messages.py --limit 100

# 2. Extract tasks, decisions, and blockers
python extract_messages.py --limit 50

# 3. View all data (with metadata annotations)
python show_db.py

# 4. Generate weekly recap
python generate_digest_cli.py
```

## CLI Tools
- `fetch_messages.py` — Fetch messages from Telegram with full metadata (reactions, threads, replies)
- `extract_messages.py` — Extract tasks/decisions/blockers via LLM
- `show_db.py` — View database content (all tables, with metadata annotations)
- `generate_digest_cli.py` — Generate weekly recap

## Configuration
Set env vars in `.env`:
- `TELEGRAM_API_ID` — Telegram API ID (from my.telegram.org)
- `TELEGRAM_API_HASH` — Telegram API Hash (from my.telegram.org)
- `TELEGRAM_PHONE` — Your phone number (with country code)
- `GROUP_CHAT_ID` — Telegram group chat ID (negative number)
- `LLM_BASE_URL` — LLM server URL (default: http://localhost:1234/v1)
- `LLM_MODEL` — Model name (optional)
- `OPENAI_API_KEY` — API key (use "dummy" for local servers)
- `DB_PATH` — SQLite database path (default: `~/.hermes/data/groupbrain.db`)

## Files
- `read_messages.py` — Fetch messages from Telegram via Telethon (with metadata)
- `fetch_messages.py` — Store messages in SQLite (with metadata)
- `extract_messages.py` — Extract tasks/decisions/blockers via LLM
- `show_db.py` — View database content (with metadata annotations)
- `generate_digest_cli.py` — Generate weekly recap
- `telegram_auth_user.py` — One-time Telegram authentication (optional)
- `extract.py` — Core LLM extraction logic
- `db.py` — SQLite storage (tasks, decisions, blockers, messages, digests)
- `digest.py` — Weekly digest generator
- `requirements.txt` — Python dependencies

## Integration with Hermes
- Uses `GROUP_CHAT_ID` from Hermes `.env`
- Cron job for weekly digest (`hermes cronjob`)

## License
Private — for internal team use only.
