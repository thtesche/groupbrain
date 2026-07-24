# Authentication

This document describes how to authenticate GroupBrain with Telegram.

## Overview

GroupBrain uses **Telethon** (not the Bot API) to read message history from a Telegram group. This requires:

1. **One-time user authentication** via `telegram_auth_user.py`
2. **Normal operation** via `read_messages.py` (no input required after session is created)

## Prerequisites

You need the following credentials from Telegram's API Development Tools:

- **API_ID** — Your Telegram API ID
- **API_HASH** — Your Telegram API Hash
- **PHONE** — Your phone number (with country code, e.g. `+4917012345678`)

### How to get API credentials

1. Go to [my.telegram.org](https://my.telegram.org) and log in with your phone number
2. Click "API Development Tools"
3. Create a new application (or use an existing one)
4. Note down your **API ID** and **API Hash**

## Setup

### 1. Configure `.env`

Edit or create the `.env` file in the groupbrain plugin directory:

```bash
# Telegram API credentials (from my.telegram.org)
TELEGRAM_API_ID=30157172
TELEGRAM_API_HASH=778309774c05ac3777f8...

# Your phone number (with country code)
TELEGRAM_PHONE=+4917012345678

# Telegram group ID (negative number for groups)
GROUP_CHAT_ID=-1004451334261
```

### 2. Install dependencies

```bash
cd ~/.hermes/plugins/groupbrain
source venv/bin/activate  # if using venv
pip install telethon python-dotenv
```

## Authentication Steps

### Step 1: One-time user authentication

Run the authentication script **once** to create the session file:

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

### Step 2: Normal operation

After the session file is created, you can run `read_messages.py` without any interaction:

```bash
python read_messages.py --limit 100
```

The script will:
1. Load the existing session file
2. Verify the session is still valid
3. Fetch messages from the group
4. Print them to the console

## Troubleshooting

### Session expires

If the session expires (e.g., after clearing cache or reinstalling), simply re-run:

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
| `telegram_auth_user.py` | One-time authentication script |
| `read_messages.py` | Main script to read messages |
| `groupbrain_session.session` | Session file (auto-created, gitignored) |
| `.env` | API credentials (gitignored) |
| `.env.example` | Example configuration (committed) |
| `.gitignore` | Excludes session files |
