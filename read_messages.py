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


async def read_messages(limit: int = 100, offset: int = 0) -> tuple[list[dict], dict[str, str]]:
    """Fetch messages from Telegram group via Telethon.
    
    Returns:
        Tuple of (messages, username_map) where username_map maps sender_id -> "first_name @username".
    """
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
        # sender_id (str) -> "first_name @username" (oder nur first_name)
        username_map: dict[str, str] = {}
        
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
            
            # Username aus sender extrahieren und im Map speichern
            if message.sender_id is not None:
                sid = str(message.sender_id)
                if sid not in username_map:
                    # message.sender ist PeerUser -> User mit username/first_name
                    if hasattr(message, 'sender') and message.sender is not None:
                        try:
                            user = await client.get_entity(message.sender)
                            # nur User-Peers haben first_name/username (nicht Chat/Channel)
                            from telethon.tl.types import User
                            if isinstance(user, User):
                                parts = []
                                if user.first_name:
                                    parts.append(user.first_name)
                                if user.username:
                                    parts.append(f"@{user.username}")
                                username_map[sid] = " ".join(parts) if parts else sid
                            else:
                                username_map[sid] = sid
                        except Exception:
                            username_map[sid] = sid
                    else:
                        username_map[sid] = sid
            
            # Reactions extrahieren
            if hasattr(message, 'reactions') and message.reactions is not None:
                reaction_labels = []
                if hasattr(message.reactions, 'results'):
                    for result in message.reactions.results:
                        emoji_str = None
                        count = getattr(result, 'count', None)
                        
                        # ReactionCount hat .reaction (ReactionEmoji oder ReactionCustomEmoji)
                        if hasattr(result, 'reaction'):
                            r = result.reaction
                            # ReactionEmoji: hat .emoticon (String)
                            if hasattr(r, 'emoticon') and r.emoticon:
                                emoji_str = r.emoticon
                            # ReactionCustomEmoji: hat .document (Document mit attributes)
                            elif hasattr(r, 'document') and r.document is not None:
                                emoji_str = f"[custom_emoji:{hex(r.document.id)}]"
                        
                        # ReactionCustomEmoji direkt auf Result (alte Struktur?)
                        elif hasattr(result, 'document') and result.document is not None:
                            emoji_str = f"[custom_emoji:{hex(result.document.id)}]"
                        
                        if emoji_str:
                            if count is not None and count > 1:
                                reaction_labels.append(f"{emoji_str}×{count}")
                            else:
                                reaction_labels.append(emoji_str)
                if reaction_labels:
                    parsed["reactions"] = reaction_labels
            
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
        
        return messages, username_map
    finally:
        await client.disconnect()


def print_messages(messages: list[dict], username_map: dict[str, str] | None = None) -> None:
    """Print messages in a readable console format.
    
    Args:
        messages: List of message dicts.
        username_map: Optional mapping of sender_id -> display name.
    """
    if username_map is None:
        username_map = {}
    
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
        
        # Username aus Map auflösen
        if sender_id is not None:
            sid_str = str(sender_id)
            display = username_map.get(sid_str, sid_str)
        else:
            display = "unbekannt"
        
        print(f"  [{date}]  message_id: {message_id}  Sender: {display}")
        
        # Wrap long text
        for i in range(0, len(text), 100):
            print(f"    {text[i:i+100]}")
        
        # Reactions
        reactions = msg.get("reactions")
        if reactions:
            reaction_str = ", ".join(reactions)
            print(f"    → Reactions: [{reaction_str}]")
        
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
    
    # Username-Zusammenfassung
    if username_map:
        print(f"\n  Username-Zusammenfassung:")
        for sid, name in sorted(username_map.items(), key=lambda x: x[1]):
            print(f"    {sid} → {name}")
    
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
    
    messages, username_map = await read_messages(limit=args.limit, offset=args.offset)
    print_messages(messages, username_map)


if __name__ == "__main__":
    asyncio.run(main())
