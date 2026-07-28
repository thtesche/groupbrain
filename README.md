# groupbrain

## Purpose
Passive knowledge extraction from Telegram group chats. Uses Telethon to fetch real messages with full metadata (reactions, threads, replies), extracts tasks/decisions/blockers via LLM, and generates weekly digests.

## Architecture
```
Telegram Group ←── read_messages.py (Telethon user client)
                    │   └── TelegramAuthUser (Auth, Session file creation)
                    │
                    ├── fetch_messages.py (CLI: calls read_messages, stores in SQLite)
                    │
                    ├── extract.py (Core module: LLM extraction via OpenAI-compatible API)
                    ├── extract_messages.py (CLI: reads from SQLite, calls LLM, stores results)
                    │
                    ├── digest.py (Core module: digest generation from SQLite)
                    ├── generate_digest_cli.py (CLI: displays digest)
                    │
                    ├── show_db.py (SQLite Viewer: messages, tasks, decisions, blockers, digests)
                    └── db.py (SQLite Schema: messages, tasks, decisions, blockers, digests, users, FTS5)

Layers:
  Telethon layer:   read_messages.py (Telegram API, User-Client, no Bot API)
  Core modules:     extract.py (LLM extraction, dataclasses), digest.py (digest generation)
  CLI wrappers:     fetch_messages.py, extract_messages.py, generate_digest_cli.py, show_db.py
  Storage:          db.py (SQLite schema + migrations)
  Orchestrator:     groupbrain.py (usage instructions)
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
- `DB_PATH` — SQLite database path (default: `data/groupbrain.db`, relativ zum Projektverzeichnis)

## Files (Core Modules)
- `read_messages.py` — Telethon user client: fetches messages with full metadata (reactions, threads, replies, forwards, media)
- `extract.py` — Core LLM extraction: sends message batches to OpenAI-compatible API, returns Task/Decision/Blocker dataclasses
- `digest.py` — Core digest generator: assembles weekly recap from tasks, decisions, blockers in SQLite

## Files (CLI Wrappers)
- `fetch_messages.py` — CLI: calls `read_messages.py`, stores messages + username mapping in SQLite
- `extract_messages.py` — CLI: reads messages from SQLite, calls `extract.py` (LLM), stores Tasks/Decisions/Blockers
- `generate_digest_cli.py` — CLI: calls `digest.py`, displays weekly recap
- `show_db.py` — CLI: SQLite Viewer (all tables: messages, tasks, decisions, blockers, digests)

## Files (Auth & Infra)
- `telegram_auth_user.py` — One-time Telegram authentication via Telethon (creates `groupbrain_session.session`)
- `groupbrain.py` — Orchestration: displays usage instructions for all CLI tools
- `db.py` — SQLite schema: messages, tasks, decisions, blockers, digests, users, FTS5 full-text search, schema migrations
- `requirements.txt` — Python dependencies

## Integration with Hermes
- Uses `GROUP_CHAT_ID` from Hermes `.env`
- Cron job for weekly digest (`hermes cronjob`)

## License
Private — for internal team use only.
