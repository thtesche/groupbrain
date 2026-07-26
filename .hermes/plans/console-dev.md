# GroupBrain Console Development Plan

## Ziel
GroupBrain-Funktionalität ohne Telegram-Bot-Anbindung entwickeln und jeden Schritt in der Konsole überprüfen.

## Bestehende, bereits unabh\u00e4ngige Module
- `db.py` — SQLite Storage (messages, tasks, decisions, blockers, digests Tables)
- `extract.py` — LLM-basierte Extraktion (Tasks, Decisions, Blocker)
- `digest.py` — Wochen-Recap Generator

## Zu schreibende CLI-Tools

### 1. `fetch_messages.py`
- **Interaktiver Console-Input** für manuelle Nachrichtenerfassung
- Schreibt direkt in `messages`-Tabelle via `db.get_db()`
- Pro Nachricht: `user_name`, `text`, `chat_id` (abfragbar)
- Bestehende Nachrichten anzeigen (Option `--list`)

### 2. `extract_messages.py`
- Liest `messages` aus SQLite (neueste N, konfigurierbar via `--limit`)
- Ruft `extract_from_messages()` aus `extract.py` auf
- Speichert Tasks/Decisions/Blocker direkt in DB
- Ausgabe: "X Tasks, Y Decisions, Z Blocker extrahiert"

### 3. `show_db.py`
- Zeigt alle Tabellen: messages, tasks, decisions, blockers, digests
- Format: lesbar in der Konsole (ähnlich wie `print_messages` aus read_messages.py)
- Optional: Filter nach Typ (`--tasks`, `--decisions`, etc.)

### 4. `generate_digest_cli.py`
- Ruft `digest.generate_digest(days)` auf
- Gibt Digest als Markdown in der Konsole aus
- Optional: `--days N` (default 7)

## Arbeitsablauf (pro Entwicklungsschritt)
```bash
# Schritt 1: fetch_messages.py erstellen und testen
python fetch_messages.py

# Schritt 2: extract_messages.py erstellen und testen
python extract_messages.py

# Schritt 3: show_db.py erstellen und testen
python show_db.py

# Schritt 4: generate_digest_cli.py erstellen und testen
python generate_digest_cli.py
```

## Bestehende Dateien (unberührt)
- `read_messages.py` — Telethon User-Client (Referenz, falls später wieder benötigt)
- `bot.py` — aiogram Bot (Referenz)
- `groupbrain.py` — Bot-Entry-Point (Referenz)
- `telegram_auth_user.py` — Telethon Auth (Referenz)
- `requirements.txt` — Abhängigkeiten
- `.env` — Konfiguration

## Open Questions
- chat_id für manuelle Eingabe: fest aus .env oder abfragbar? → Fest aus .env (GROUP_CHAT_ID)
- LLM-Konfiguration: bereits in extract.py über Environment-Variablen gelöst
