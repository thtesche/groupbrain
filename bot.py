"""
Telegram Bot — long-polling mode.
Listens to group messages, extracts tasks/decisions/blockers via LLM,
stores in SQLite. Posts weekly digest via cron.
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode

from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from db import get_db
from extract import extract_from_messages, Task, Decision, Blocker
from digest import generate_digest, save_digest

# Load env
load_dotenv(Path(__file__).parent / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
if not BOT_TOKEN or not GROUP_CHAT_ID:
    print("ERROR: TELEGRAM_BOT_TOKEN and GROUP_CHAT_ID must be set in .env")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# --- DM handling (direct interaction with bot) ---

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Show help message."""
    await message.answer(
        "🤖 **GroupBrain Bot**\n\n"
        "**Commands:**\n"
        "/tasks — Show all open tasks\n"
        "/decisions — Show all decisions\n"
        "/blockers — Show active blockers\n"
        "/digest — Generate and send weekly digest\n"
        "/status — Show bot status\n"
        "/import-whatsapp — Import WhatsApp backup\n\n"
        "**In the group:**\n"
        "The bot passively observes messages and extracts:\n"
        "• Tasks (action items, assignments)\n"
        "• Decisions (choices, conclusions)\n"
        "• Blockers (obstacles, problems)\n\n"
        "Just chat normally — no extra effort needed."
    )


@dp.message(Command("tasks"))
async def cmd_tasks(message: types.Message):
    """Show all open tasks."""
    conn = get_db()
    tasks = conn.execute(
        "SELECT title, author, status, created_at FROM tasks WHERE status != 'done' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    if not tasks:
        await message.answer("📋 Keine offenen Tasks.")
        return

    lines = ["**📌 Offene Tasks:**\n"]
    for t in tasks:
        lines.append(f"- {t[0]} (@{t[1]}) — {t[3][:10]}")

    await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


@dp.message(Command("decisions"))
async def cmd_decisions(message: types.Message):
    """Show all decisions."""
    conn = get_db()
    decisions = conn.execute(
        "SELECT topic, decision, author, created_at FROM decisions ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()

    if not decisions:
        await message.answer("📝 Keine Entscheidungen gespeichert.")
        return

    lines = ["**✅ Entscheidungen:**\n"]
    for d in decisions:
        lines.append(f"- **{d[0]}**: {d[1]} (@{d[2]})")

    await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


@dp.message(Command("blockers"))
async def cmd_blockers(message: types.Message):
    """Show active blockers."""
    conn = get_db()
    blockers = conn.execute(
        "SELECT title, reporter, created_at FROM blockers WHERE status = 'active' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    if not blockers:
        await message.answer("🟢 Keine aktiven Blocker.")
        return

    lines = ["**🚧 Aktive Blocker:**\n"]
    for b in blockers:
        lines.append(f"- {b[0]} (von @{b[1]})")

    await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


@dp.message(Command("digest"))
async def cmd_digest(message: types.Message):
    """Generate and send weekly digest."""
    content = generate_digest(7)
    await message.answer(content, parse_mode=ParseMode.MARKDOWN)
    save_digest(content, str(message.chat.id))


@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    """Show bot status."""
    conn = get_db()
    task_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    decision_count = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    blocker_count = conn.execute("SELECT COUNT(*) FROM blockers WHERE status = 'active'").fetchone()[0]
    message_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    conn.close()

    status = (
        f"🤖 **GroupBrain Status**\n\n"
        f"📩 Messages: {message_count}\n"
        f"📌 Tasks: {task_count}\n"
        f"✅ Decisions: {decision_count}\n"
        f"🚧 Active Blockers: {blocker_count}\n"
        f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await message.answer(status, parse_mode=ParseMode.MARKDOWN)


@dp.message(Command("import-whatsapp"))
async def cmd_import_whatsapp(message: types.Message):
    """Import WhatsApp backup."""
    try:
        from whatsapp import import_all
        count = import_all()
        await message.answer(f"✅ {count} WhatsApp messages imported.")
    except ImportError:
        await message.answer("WhatsApp import not available. Install dependencies.")


# --- Group message handler (passive observation via LLM) ---

@dp.message()
async def handle_message(message: types.Message):
    """Handle incoming messages — store and extract via LLM."""
    # Skip bot's own messages
    if message.from_user and message.from_user.is_bot:
        return

    # Skip very short messages (emojis, greetings)
    if message.text and len(message.text.strip()) < 3:
        return

    user_name = message.from_user.username or message.from_user.first_name or "unknown"

    # Store message in database
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO messages (chat_id, message_id, user_id, user_name, source, text) VALUES (?, ?, ?, ?, 'telegram', ?)",
            (str(message.chat.id), message.message_id, str(message.from_user.id), user_name, message.text)
        )
        conn.commit()
    finally:
        conn.close()

    # Extract from batch of recent messages using LLM
    conn = get_db()
    try:
        recent = conn.execute(
            "SELECT message_id, user_name, text, chat_id FROM messages "
            "WHERE chat_id = ? ORDER BY id DESC LIMIT 20",
            (str(message.chat.id),)
        ).fetchall()

        # Convert to dict format for extract_from_messages
        messages = []
        for row in recent:
            messages.append({
                "message_id": row[0],
                "user_name": row[1],
                "text": row[2],
                "chat_id": row[3],
            })

        results = extract_from_messages(messages)

        if results:
            for result in results:
                for task in result.tasks:
                    conn.execute(
                        "INSERT INTO tasks (title, author, source_message_id, source_chat_id) VALUES (?, ?, ?, ?)",
                        (task.title, task.author, task.source_message_id, task.source_chat_id)
                    )

                for decision in result.decisions:
                    conn.execute(
                        "INSERT INTO decisions (topic, decision, author, source_message_id, source_chat_id) VALUES (?, ?, ?, ?, ?)",
                        (decision.topic, decision.decision, decision.author, decision.source_message_id, decision.source_chat_id)
                    )

                for blocker in result.blockers:
                    conn.execute(
                        "INSERT INTO blockers (title, reporter, source_message_id, source_chat_id) VALUES (?, ?, ?, ?)",
                        (blocker.title, blocker.reporter, blocker.source_message_id, blocker.source_chat_id)
                    )

                conn.commit()

                # Notify in group on blockers
                if result.blockers:
                    await message.answer(
                        f"🚧 Blocker erkannt: {result.blockers[0].title}\n"
                        f"(@{result.blockers[0].reporter} hat dies gemeldet.)",
                        parse_mode=ParseMode.MARKDOWN
                    )
    finally:
        conn.close()


async def on_startup(bot: Bot):
    """Log startup."""
    logger.info(f"GroupBrain Bot started. Listening to group: {GROUP_CHAT_ID}")


async def on_shutdown(bot: Bot):
    """Cleanup on shutdown."""
    await bot.session.close()


def main():
    """Run the bot."""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Register all command handlers
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_tasks, Command("tasks"))
    dp.message.register(cmd_decisions, Command("decisions"))
    dp.message.register(cmd_blockers, Command("blockers"))
    dp.message.register(cmd_digest, Command("digest"))
    dp.message.register(cmd_status, Command("status"))
    dp.message.register(cmd_import_whatsapp, Command("import-whatsapp"))

    # Main message handler (passive observation)
    dp.message.register(handle_message)

    # Start polling
    logger.info(f"Starting long-polling for group: {GROUP_CHAT_ID}")
    dp.run_polling(bot, allowed_updates=types.Update.all_update_types())


if __name__ == "__main__":
    main()
