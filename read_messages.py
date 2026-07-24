#!/usr/bin/env python3
"""
Read historical messages from a Telegram group and print them to console.
Usage: python read_messages.py [--limit 100] [--offset 0]
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv(Path(__file__).parent / ".env")

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

if not all([API_ID, API_HASH, GROUP_CHAT_ID]):
    print("ERROR: TELEGRAM_API_ID, TELEGRAM_API_HASH, and GROUP_CHAT_ID must be set in .env")
    sys.exit(1)


async def read_messages(limit: int = 100, offset: int = 0) -> list[dict]:
    """Fetch messages from Telegram group via Telethon."""
    # Erstelle den Client als normaler Telegram-Nutzer (nicht Bot)
    client = TelegramClient('groupbrain_session', int(API_ID or "0"), API_HASH or "")
    
    try:
        # Verbinde mit der bestehenden Session (keine Eingabe nötig)
        await client.connect()
        
        # Prüfe, ob Session gültig ist
        if not await client.is_user_authorized():
            print("ERROR: Session nicht gültig. Führe 'python telegram_auth_user.py' aus.")
            sys.exit(1)
        
        chat_id = int(GROUP_CHAT_ID or "0")
        
        messages = []
        async for message in client.iter_messages(
            chat_id,
            limit=limit,
            offset_id=offset,
            min_id=0,
            reverse=True  # Älteste zuerst
        ):
            parsed = {
                "message_id": message.id,
                "date": message.date.isoformat(),
                "sender_id": message.sender_id,
                "text": message.text or "[keine Textnachricht]",
            }
            
            # Reply- und Thread-Information (nur echte Telegram-Replies, keine Zitate)
            # message.is_reply kann True sein für Zitate - wir prüfen den Typ
            if message.is_reply and message.reply_to:
                reply_type = type(message.reply_to).__name__
                # ReplyToMessage für normale Gruppen, MessageReplyHeader für Forum-Topics
                if reply_type in ('ReplyToMessage', 'MessageReplyHeader'):
                    reply_to_msg_id = message.reply_to.reply_to_msg_id
                    
                    # Thread-ID: reply_to_top_id ist die Root-Nachricht (Thread-Start)
                    # Falls None (direkte Antwort auf Root), ist reply_to_msg_id selbst die Thread-ID
                    top_id = getattr(message.reply_to, 'reply_to_top_id', None)
                    parsed["thread_id"] = top_id if top_id is not None else reply_to_msg_id
                    
                    # Forum-Topic: Boolean, ob es ein echtes Topic in einer Supergruppe ist
                    parsed["is_forum_topic"] = getattr(message.reply_to, 'forum_topic', False)
                    
                    # Direkte Antwort-ID (für verschachtelte Zitate innerhalb des Threads)
                    parsed["reply_to_id"] = reply_to_msg_id
            
            # Forward-Informationen
            if message.forward:
                parsed["forwarded"] = True
                if hasattr(message.forward, 'sender_user_id'):
                    parsed["forward_from"] = message.forward.sender_user_id
                elif hasattr(message.forward, 'from_id'):
                    parsed["forward_from"] = message.forward.from_id
            
            # Medien (Fotos, Dokumente)
            if message.file:
                parsed["has_media"] = True
                parsed["media_type"] = type(message.file).__name__
            
            # Interaktive Buttons
            if message.buttons:
                parsed["button_count"] = message.button_count
            
            messages.append(parsed)
        
        return messages
    finally:
        await client.disconnect()


def print_messages(messages: list[dict]) -> None:
    """Print messages in a readable console format."""
    if not messages:
        print("Keine Nachrichten gefunden.")
        return
    
    print(f"\n{'='*70}")
    print(f"  Telegram Group Messages  ({len(messages)} Nachrichten)")
    print(f"{'='*70}\n")
    
    for msg in messages:
        date = msg["date"]
        message_id = msg["message_id"]
        sender_id = msg["sender_id"]
        text = msg["text"]
        
        print(f"  [{date}]  message_id: {message_id}  Sender_ID: {sender_id}")
        
        # Wrap long text
        for i in range(0, len(text), 100):
            print(f"    {text[i:i+100]}")
        
        # Reply-Information
        if "reply_to_id" in msg:
            print(f"    → Reply zu Nachricht {msg['reply_to_id']}")
        
        # Thread-Information
        if "thread_id" in msg:
            ft = "Forum-Topic" if msg.get("is_forum_topic") else "normaler Thread"
            print(f"    → Thread-ID: {msg['thread_id']} ({ft})")
        
        # Forward-Information
        if msg.get("forwarded"):
            forward_from = msg.get("forward_from")
            print(f"    → Forwarded (from: {forward_from})")
        
        # Medien-Information
        if msg.get("has_media"):
            media_type = msg.get("media_type", "unknown")
            print(f"    → Media: {media_type}")
        
        # Button-Information
        if "button_count" in msg:
            print(f"    → Buttons: {msg['button_count']}")
        
        print()
    
    # Thread-Zusammenfassung
    thread_summary = {}
    for msg in messages:
        tid = msg.get("thread_id")
        if tid is not None:
            if tid not in thread_summary:
                thread_summary[tid] = {"count": 0, "is_forum_topic": msg.get("is_forum_topic", False)}
            thread_summary[tid]["count"] += 1
    
    if thread_summary:
        print(f"\n  Thread-Zusammenfassung:")
        for tid, info in thread_summary.items():
            ft = "Forum-Topic" if info["is_forum_topic"] else "normaler Thread"
            print(f"    Thread {tid}: {info['count']} Nachrichten ({ft})")
    
    print(f"\n{'='*70}")
    print(f"  Gesamt: {len(messages)} Nachrichten")
    print(f"{'='*70}\n")


async def main():
    parser = argparse.ArgumentParser(description="Read messages from Telegram group")
    parser.add_argument("--limit", type=int, default=100, help="Max messages to fetch (default: 100)")
    parser.add_argument("--offset", type=int, default=0, help="Message offset for pagination (default: 0)")
    args = parser.parse_args()
    
    print(f"📩 Lese Nachrichten aus Gruppe: {GROUP_CHAT_ID}")
    print(f"   Limit: {args.limit}, Offset: {args.offset}\n")
    
    messages = await read_messages(limit=args.limit, offset=args.offset)
    print_messages(messages)


if __name__ == "__main__":
    asyncio.run(main())
