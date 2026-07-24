#!/usr/bin/env python3
"""
Einmalige Telegram-Authentifizierung für GroupBrain.
Erstellt die Session-Datei 'groupbrain_session.session' für den Chat-Historie-Export.

Nutzung: python telegram_auth_user.py
"""
import os
import sys
import getpass
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Lade .env aus groupbrain plugin
load_dotenv(Path(__file__).parent / ".env")

# Hole die Zugangsdaten aus den Umgebungsvariablen
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

if not all([API_ID, API_HASH, PHONE]):
    print("FEHLER: TELEGRAM_API_ID, TELEGRAM_API_HASH und TELEGRAM_PHONE müssen gesetzt sein.")
    sys.exit(1)

async def auth_once():
    # Erstellt die Session-Datei 'groupbrain_session.session'
    client = TelegramClient('groupbrain_session', int(API_ID or "0"), API_HASH or "")
    
    print("Verbinde mit Telegram...")
    await client.connect()

    if await client.is_user_authorized():
        print("Du bist bereits authentifiziert! Die .session-Datei ist bereits gültig.")
        return

    print(f"Sende Login-Code an {PHONE}...")
    await client.send_code_request(PHONE)
    
    code = input("Bitte gib den 5-stelligen Code ein (aus der Telegram-App oder per SMS): ")

    try:
        # Versuche den Login nur mit dem Code
        await client.sign_in(PHONE, code)
        print("Erfolgreich eingeloggt (Ohne 2FA)!")
        
    except SessionPasswordNeededError:
        # Dieser Block wird ausgeführt, wenn 2FA aktiviert ist
        print("\nSchritt 2: 2-Faktor-Authentifizierung (2FA) ist aktiviert.")
        password = getpass.getpass("Bitte gib dein Cloud-Passwort ein (Eingabe bleibt unsichtbar): ")
        
        await client.sign_in(password=password)
        print("Erfolgreich mit 2FA eingeloggt!")

    print("\n✅ Authentifizierung abgeschlossen!")
    print("Die Datei 'groupbrain_session.session' wurde in diesem Ordner erstellt.")
    print("Du kannst diese Datei nun auf deinen Server kopieren. Dein Hauptskript wird danach keine Eingaben mehr verlangen.")

if __name__ == '__main__':
    # Startet die asynchrone Funktion
    asyncio.run(auth_once())
