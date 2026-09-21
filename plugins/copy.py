import logging
import asyncio
from pyrogram.errors import FloodWait
from pyrogram import Client, filters, enums

logger = logging.getLogger(__name__)
media_filter = filters.video | filters.document

# Strict FIFO queue – processes messages in the exact order handlers received them
_forward_queue: asyncio.Queue = None
_worker_task = None


async def _process_one(bot, chat, message, db_crash: bool):
    """Copy a single message. Runs only inside the sequential worker."""
    try:
        try:
            await bot.copy_message(
                chat_id=chat,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=f"**{message.caption or ''}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        except FloodWait as e:
            logger.warning(f"⏳ FloodWait: sleeping {e.value}s for msg {message.id}")
            await asyncio.sleep(e.value)
            await bot.copy_message(
                chat_id=chat,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=f"**{message.caption or ''}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )

        # Small delay so we don't hammer Telegram too hard
        await asyncio.sleep(0.6)

        if not db_crash:
            try:
                await bot.db.increment_stat("forwarded")
            except Exception as e:
                logger.error(f"❌ Forwarded stat error: {e}")

        logger.info(f"✅ Forwarded msg {message.id} from {message.chat.id}")

    except Exception as e:
        logger.error(f"❌ Failed to forward msg {message.id}: {e}")


async def _forward_worker(bot):
    """Single background worker – guarantees order."""
    logger.info("🚀 Forward worker started (strict FIFO)")
    while True:
        try:
            item = await _forward_queue.get()
            if item is None:          # shutdown signal
                break

            chat, message, db_crash = item
            await _process_one(bot, chat, message, db_crash)
            _forward_queue.task_done()

        except asyncio.CancelledError:
            logger.info("🛑 Forward worker cancelled")
            break
        except Exception as e:
            logger.error(f"❌ Worker error: {e}")
            # continue so one bad message doesn't kill the whole queue


def start_forward_worker(bot):
    """Call this once from UserBot.start()"""
    global _forward_queue, _worker_task
    if _forward_queue is None:
        _forward_queue = asyncio.Queue()
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(_forward_worker(bot))
        logger.info("✅ Forward worker task created")


@Client.on_message(filters.channel & media_filter)
async def forward_media(bot, message):
    try:
        # Ensure worker is running (safety net)
        if _forward_queue is None:
            start_forward_worker(bot)

        try:
            chat = await bot.db.get_channel()
        except Exception as e:
            chat = -1001912424642  # Fallback
            logger.error(f"❌ Could not get channel: {e}")

        if not chat:
            return

        if message.chat.id == chat:
            return

        file_unique_id = None
        if message.video:
            file_unique_id = message.video.file_unique_id
        elif message.document:
            file_unique_id = message.document.file_unique_id

        if not file_unique_id:
            return

        # Duplicate check (still done in parallel – fast)
        result = None
        db_crash = False
        try:
            result = await bot.db.add_media(file_unique_id)
        except Exception as e:
            db_crash = True
            logger.error(f"❌ DB add_media failed: {e}")

        if result == "duplicate":
            logger.info(f"🚫 Duplicate skipped: {file_unique_id}")
            try:
                await bot.db.increment_stat("duplicates")
            except Exception as e:
                logger.error(f"❌ Duplicate stat error: {e}")
            return

        # Enqueue for sequential copy – this is what preserves order
        await _forward_queue.put((chat, message, db_crash))

    except Exception as e:
        logger.error(f"❌ Handler error: {e}")
