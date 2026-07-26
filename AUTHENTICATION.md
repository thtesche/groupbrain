# Authentication

This document describes how to authenticate GroupBrain with Telegram (optional).

## Overview

GroupBrain can operate in two modes:

1. **Console mode** (default) — Manual message entry via CLI tools. No Telegram connection needed.
2. **Telegram mode** (optional) — Automatic message extraction from a Telegram group via Telethon.

## Console Mode (No Telegram Required)

The 4 CLI tools work independently of Telegram:

| Tool | Purpose | Usage |
|------|---------|-------|
| `fetch_messages.py` | Enter messages manually | `python fetch_messages.py` |
| `extract_messages.py` | Extract tasks/decisions/blockers | `python extract_messages.py [--limit 50]` |
| `show_db.py` | Display all database content | `python show_db.py [--tasks|--blockers|--messages]` |
| `generate_digest_cli.py` | Generate weekly recap | `python generate_digest_cli.py [--days 14]` |

Full pipeline:

```bash
python fetch_messages.py              # Enter messages interactively
python extract_messages.py            # Extract tasks/decisions/blockers
python show_db.py                     # View all data
python generate_digest_cli.py         # Generate weekly recap
```

## Telegram Mode (Optional)

For automatic message extraction from Telegram, GroupBrain uses **Telethon** (not the Bot API). This requires:

1. **One-time user authentication** via `telegram_auth_user.py`
2. **Message extraction** via `read_messages.py` (deprecated — use `fetch_messages.py` instead)

### Prerequisites

You need the following credentials from Telegram's API Development Tools:

- **API_ID** — Your Telegram API ID
- **API_HASH** — Your Telegram API Hash
- **PHONE** — Your phone number (with country code, e.g. `+491****5678`)

### How to get API credentials

1. Go to [my.telegram.org](https://my.telegram.org) and log in with your phone number
2. Click "API Development Tools"
3. Create a new application (or use an existing one)
4. Note down your **API ID** and **API Hash**

### Setup

1. Configure `.env`:

```bash
# Telegram API credentials (from my.telegram.org)
TELEGRAM_API_ID=30157172
TELEGRAM_API_HASH=778309774c05ac3777f8...

# Your phone number (with country code)
TELEGRAM_PHONE=+491****5678

# Telegram group ID (negative number for groups)
GROUP_CHAT_ID=-1004451334261
```

2. Install dependencies:

```bash
cd ~/.hermes/plugins/groupbrain
source venv/bin/activate
pip install telethon python-dotenv
```

### Authentication Steps

**Step 1: One-time user authentication**

```bash
python telegram_auth_user.py
```

This script will:
1. Connect to Telegram using your API credentials
2. Send a 5-digit code to your phone number
3. Prompt you to enter the code from the Telegram app (or SMS)
4. If 2FA is enabled, prompt for your cloud password
5. Create the file `groupbrain_session.session` in the current directory

**Note:** The session file is automatically excluded from version control via `.gitignore`.

## Troubleshooting

### Session expires

If the session expires, re-run:

```bash
python telegram_auth_user.py
```

### "BotMethodInvalidError: getHistory not allowed"

This error occurs when trying to use the Bot API instead of a user session. Make sure you're using the user authentication method (not bot token authentication).

### Missing dependencies

If you see `ModuleNotFoundError: No module named 'pyasn1'`, install it:

```bash
pip install pyasn1
```

## Files

| File | Purpose |
|------|---------|
| `fetch_messages.py` | Enter messages manually (Console mode) |
| `extract_messages.py` | Extract tasks/decisions/blockers (Console mode) |
| `show_db.py` | Display database content (Console mode) |
| `generate_digest_cli.py` | Generate weekly recap (Console mode) |
| `telegram_auth_user.py` | One-time Telegram authentication (optional) |
| `groupbrain_session.session` | Session file (auto-created, gitignored) |
| `.env` | API credentials (gitignored) |
| `.env.example` | Example configuration (committed) |
| `.gitignore` | Excludes session files |
