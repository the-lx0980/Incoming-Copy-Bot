import logging
import asyncio
import heapq
from pyrogram.errors import FloodWait
from pyrogram import Client, filters, enums

logger = logging.getLogger(__name__)
media_filter = filters.video | filters.document

# Sequential processing to preserve message order during bulk uploads
_pending = []                 # min-heap of (message_id, counter, item)
_counter = 0                  # tie-breaker for heap
_lock = asyncio.Lock()
_worker_running = False
_CONDITION = asyncio.Condition()


async def _process_one(bot, chat, message, file_unique_id, db_crash):
    """Actually copy one message (runs only inside the sequential worker)."""
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
            logger.warning(f"⏳ FloodWait triggered. Sleeping for {e.value} seconds.")
            await asyncio.sleep(e.value)
            await bot.copy_message(
                chat_id=chat,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=f"**{message.caption or ''}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )

        # Small delay to avoid hammering Telegram
        await asyncio.sleep(0.8)

        if not db_crash:
            try:
                await bot.db.increment_stat("forwarded")
            except Exception as e:
                logger.error(f"❌ Forwarded Increment Error: {e}")

    except Exception as e:
        logger.error(f"❌ Forward of msg {message.id} failed: {e}")


async def _worker(bot):
    """Single background worker that always processes the lowest message_id first."""
    global _worker_running
    try:
        while True:
            async with _CONDITION:
                # Wait until there is at least one item
                while not _pending:
                    await _CONDITION.wait()

                # Always take the smallest message_id (preserves original order)
                _, _, item = heapq.heappop(_pending)

            chat, message, file_unique_id, db_crash = item
            await _process_one(bot, chat, message, file_unique_id, db_crash)

    except asyncio.CancelledError:
        logger.info("🛑 Forward worker cancelled")
    except Exception as e:
        logger.error(f"❌ Forward worker crashed: {e}")
    finally:
        _worker_running = False


async def _ensure_worker(bot):
    global _worker_running
    async with _lock:
        if not _worker_running:
            _worker_running = True
            asyncio.create_task(_worker(bot))


@Client.on_message(filters.channel & media_filter)
async def forward_media(bot, message):
    try:
        try:
            chat = await bot.db.get_channel()
        except Exception as e:
            chat = -1001912424642  # Fallback channel ID
            logger.error(f"❌ Database Couldn't find Channel id Error: {e}")

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

        result = None
        db_crash = False
        try:
            result = await bot.db.add_media(file_unique_id)
        except Exception as e:
            db_crash = True
            logger.error(f"❌ Database Operation failed: {e}")

        if result == "duplicate":
            logger.info(f"🚫 Duplicate media detected ({file_unique_id}). Skipping forward.")
            try:
                await bot.db.increment_stat("duplicates")
            except Exception as e:
                logger.error(f"❌ Duplicate Stat increment failed: {e}")
            return

        # Enqueue instead of copying immediately → preserves order
        global _counter
        item = (chat, message, file_unique_id, db_crash)

        async with _CONDITION:
            heapq.heappush(_pending, (message.id, _counter, item))
            _counter += 1
            _CONDITION.notify()

        await _ensure_worker(bot)

    except Exception as e:
        logger.error(f"❌ Forwarding core pipeline failed: {e}")
