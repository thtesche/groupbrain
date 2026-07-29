#!/usr/bin/env python3
"""
One-time Telegram authentication for GroupBrain.
Creates the session file 'groupbrain_session.session' for chat history export.

Usage: python telegram_auth_user.py
"""
import os
import sys
import getpass
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Load .env from project directory
load_dotenv(Path(__file__).parent / ".env")

# Get credentials from environment variables
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

if not all([API_ID, API_HASH, PHONE]):
    print("ERROR: TELEGRAM_API_ID, TELEGRAM_API_HASH and TELEGRAM_PHONE must be set.")
    sys.exit(1)

async def auth_once():
    # Creates the session file 'groupbrain_session.session'
    client = TelegramClient('groupbrain_session', int(API_ID or "0"), API_HASH or "")
    
    print("Connecting to Telegram...")
    await client.connect()

    if await client.is_user_authorized():
        print("You are already authenticated! The .session file is already valid.")
        return

    print(f"Sending login code to {PHONE}...")
    await client.send_code_request(PHONE)
    
    code = input("Please enter the 5-digit code (from the Telegram app or SMS): ")

    try:
        # Attempt login with code only
        await client.sign_in(PHONE, code)
        print("Logged in successfully (without 2FA)!")
        
    except SessionPasswordNeededError:
        # This block executes if 2FA is enabled
        print("\nStep 2: Two-factor authentication (2FA) is enabled.")
        password = getpass.getpass("Please enter your cloud password (input is hidden): ")
        
        await client.sign_in(password=password)
        print("Logged in successfully with 2FA!")

    print("\n✅ Authentication complete!")
    print("The file 'groupbrain_session.session' has been created in this directory.")
    print("You can copy this file to your server. Your main script will not require further input.")

if __name__ == '__main__':
    # Start the async function
    asyncio.run(auth_once())
