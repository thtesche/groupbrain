#!/usr/bin/env python3
"""
GroupBrain — Telegram API client for sending digests.

Handles sending digest messages to Telegram groups via Telethon user client,
including message splitting for large digests and session health checks.

Usage:
    from telegram_client import send_digest_to_telegram, check_session_health
"""
import os
import logging
from pathlib import Path
from telethon import TelegramClient

logger = logging.getLogger(__name__)

TELEGRAM_MAX_LENGTH = 4000
SESSION_FILE = "groupbrain_session"


def split_digest(text: str, max_len: int = TELEGRAM_MAX_LENGTH) -> list[str]:
    """Split markdown digest into chunks that fit Telegram's 4096 limit."""
    chunks = []
    current = ""

    for paragraph in text.split("\n\n"):
        if current and len(current) + 2 + len(paragraph) > max_len:
            chunks.append(current)
            current = paragraph
        elif len(paragraph) > max_len:
            while len(paragraph) > max_len:
                split_at = paragraph.rfind(" ", 0, max_len)
                if split_at == -1:
                    split_at = max_len
                chunks.append(paragraph[:split_at])
                paragraph = paragraph[split_at:].lstrip()
            current = paragraph if paragraph else ""
        else:
            current = current + "\n\n" + paragraph if current else paragraph

    if current:
        chunks.append(current)

    return chunks


async def check_session_health(api_id: str, api_hash: str) -> tuple[bool, str]:
    """Check if the Telegram session is valid.

    Returns:
        Tuple of (is_valid, message).
    """
    client = TelegramClient(SESSION_FILE, int(api_id), api_hash)

    try:
        await client.connect()
        is_authorized = await client.is_user_authorized()
        await client.disconnect()

        if is_authorized:
            return True, "Session is valid."
        else:
            return False, (
                "Session invalid or expired. Run 'python telegram_auth_user.py' to re-authenticate."
            )

    except Exception as e:
        await client.disconnect()
        logger.error(f"Session health check failed: {e}")
        return False, f"Connection error: {e}"


async def send_digest_to_telegram(
    digest_text: str,
    chat_id: str,
    api_id: str,
    api_hash: str,
) -> bool:
    """Send digest to Telegram group, splitting into chunks if necessary.

    Args:
        digest_text: The digest content to send.
        chat_id: Telegram group chat ID.
        api_id: Telegram API ID.
        api_hash: Telegram API Hash.

    Returns:
        True if sent successfully, False otherwise.
    """
    client = TelegramClient(SESSION_FILE, int(api_id), api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            msg = "[!] ERROR: Session invalid. Run 'python telegram_auth_user.py'."
            print(msg)
            logger.error(msg)
            return False

        chunks = split_digest(digest_text)

        if len(chunks) > 1:
            print(f"[*] Digest split into {len(chunks)} message(s).")
        else:
            print("[*] Sending digest as single message...")

        for i, chunk in enumerate(chunks):
            prefix = f"(Part {i+1}/{len(chunks)}) " if len(chunks) > 1 else ""
            await client.send_message(int(chat_id), prefix + chunk, parse_mode="markdown")
            print(f"  ✓ Sent: Part {i+1}/{len(chunks)} ({len(chunk)} chars)")

        print("[+] Digest sent successfully.")
        logger.info("Digest sent successfully to chat %s", chat_id)
        return True

    except Exception as e:
        logger.error(f"Failed to send digest: {e}")
        print(f"[!] Error sending digest: {e}")
        return False

    finally:
        await client.disconnect()
