import logging
from pyrogram import filters
from config import Config

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start") & filters.user(Config.ADMINS))
async def start_cmd(bot, message):
    await message.reply_text(
        "🤖 <b>Bot Status:</b> <code>Zinda Hain!</code>\n"
        "✅ Ready to forward!\n\n"
        "<b>Commands</b>\n"
        "/stats: check stats\n"
        "/cleardb: clear database",
    )


@Client.on_message(filters.command("stats") & filters.user(Config.ADMINS))
async def show_total(bot, message):
    """
    Shows how many media have been forwarded and how many duplicates blocked.
    """
    try:
        stats = await bot.db.get_stats()
        text = (
            "📊 <b>Bot Statistics</b>\n\n"
            f"✅ Forwarded: <code>{stats['forwarded']}</code>\n"
            f"🚫 Duplicates Blocked: <code>{stats['duplicates']}</code>\n"
            f"📦 Total in DB: <code>{stats['total']}</code>"
        )
        await message.reply_text(text)
    except Exception as e:
        logger.error(f"❌ Error fetching stats: {e}")
        await message.reply_text("⚠️ Failed to fetch stats.")


@Client.on_message(filters.command("cleardb") & filters.user(Config.ADMINS))
async def clear_database(bot, message):
    """
    Clears all records and stats from the database.
    """
    try:
        await bot.db.clear_all()
        await message.reply_text("🧹 Database cleared successfully.")
        logger.info("🧹 Database cleared by command.")
    except Exception as e:
        logger.error(f"❌ Failed to clear database: {e}")
        await message.reply_text("⚠️ Failed to clear database.")
