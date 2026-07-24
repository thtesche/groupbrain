# groupbrain

## Purpose
Passive knowledge extraction from Telegram group chats. No manual documentation needed — the bot observes, extracts, and surfaces what matters.

## Architecture
```
Telegram Group ←── Bot (Long-Polling)
                    ├── extract.py  (Pattern + LLM)
                    ├── db.py       (SQLite Storage)
                    └── digest.py   (Weekly Digest)
```

## Quick Start
```bash
cd ~/.hermes/plugins/groupbrain
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=your_token
export GROUP_CHAT_ID=-1004451334261
python bot.py
```

## Features
- **Task Extraction**: Detects TODO items in chat
- **Decision Logging**: Captures team decisions with context
- **Blocker Tracking**: Identifies blocked items
- **Weekly Digest**: Auto-generates and posts summary
- **WhatsApp Import**: Parses chat backups as secondary source

## Configuration
Set env vars in `.env`:
- `TELEGRAM_BOT_TOKEN` — Bot API token from @BotFather
- `GROUP_CHAT_ID` — Telegram group chat ID (negative number)
- `DB_PATH` — SQLite database path (default: `~/.hermes/data/groupbrain.db`)

## Files
- `bot.py` — Telegram bot (long-polling, message handler)
- `extract.py` — Task/Decision/Blocker extraction (regex + LLM)
- `db.py` — SQLite storage (tasks, decisions, blockers, messages, digests)
- `digest.py` — Weekly digest generator
- `whatsapp.py` — WhatsApp chat backup parser
- `requirements.txt` — Python dependencies

## Integration with Hermes
- Uses `TELEGRAM_BOT_TOKEN` from Hermes `.env`
- Can call Hermes tools via API (session_search, memory)
- Cron job for weekly digest (`hermes cronjob`)

## License
Private — for internal team use only.
