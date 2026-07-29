import logging
from pyrogram import filters
from config import Config
from pyrogram.errors import UserNotParticipant
from pyrogram import Client, filters

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start") & filters.user(Config.ADMINS))
async def start_cmd(bot, message):
    """Simple check to confirm bot is alive and running."""
    await message.reply_text(
        "🤖 <b>Bot Status:</b> <code>✅ Zinda Hai!</code>\n"
        "⚙️ <b>System:</b> Ready to forward media.\n\n"
        "📋 <b>Available Commands:</b>\n"
        "• /stats → Show forwarding statistics\n"
        "• /cleardb → Clear all saved records\n"
        "• /add_chat → Set forward destination\n"
        "• /delete_chat → Remove current chat\n"
        "• /show_chat → Display current chat"
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

@Client.on_message(filters.command("add_chat") & filters.user(Config.ADMINS))
async def add_channel_cmd(bot, message):
    """Add one chat for forwarding"""
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: `/add_chat <chat_id>`")

    try:
        channel_id = int(message.command[1])
        
        try:
            chat = await bot.get_chat(channel_id)
        except UserNotParticipant:
            return await message.reply_text("🚫 Userbot must be a member of that chat first!")
        except Exception as e:
            return await message.reply_text(f"❌ Error:\n{e}")

        await bot.db.set_channel(chat.id)
        await message.reply_text(f"✅ Chat added for forwarding:\n<b>{chat.title}</b> (<code>{chat.id}</code>)")
            
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
            


@Client.on_message(filters.command("delete_chat") & filters.user(Config.ADMINS))
async def delete_channel_cmd(bot, message):
    """Delete the saved forward chat"""
    await bot.db.delete_channel()
    await message.reply_text("🗑️ Forward channel deleted.")
        

@Client.on_message(filters.command("show_chat") & filters.user(Config.ADMINS))
async def show_channel_cmd(bot, message):
    """Show the currently set chat"""
    try:
        channel_id = await bot.db.get_channel()
        if not channel_id:
            return await message.reply_text("⚠️ No forward channel set yet.")
                
        try:
            chat = await bot.get_chat(channel_id)
            status = f"✅ Active: <b>{chat.title}</b> (<code>{chat.id}</code>)"
        except Exception as e:
            status = f"⚠️ Can't access chat: {e}"

        await message.reply_text(f"📡 Current forward chat:\n<b>ID:</b> <code>{channel_id}</code>\n<b>Status:</b> {status}")
            
    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
            
