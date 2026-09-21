import logging
import asyncio
from pyrogram.errors import FloodWait
from pyrogram import Client, filters, enums

logger = logging.getLogger(__name__)
media_filter = filters.video | filters.document

# ============================================================
# STRICT ORDER PRESERVATION
# Telegram can deliver updates out-of-order when many files
# are uploaded at once. We therefore always process by
# ascending message.id (the true order they exist in the chat).
# ============================================================

_priority_queue: asyncio.PriorityQueue = None
_worker_task = None
_seq = 0                       # tie-breaker so equal IDs don't compare Message objects
_seq_lock = asyncio.Lock()


async def _process_one(bot, chat: int, message, db_crash: bool):
    """Actually copy the message. Called only by the single worker."""
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
            logger.warning(f"⏳ FloodWait {e.value}s – msg {message.id}")
            await asyncio.sleep(e.value)
            await bot.copy_message(
                chat_id=chat,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=f"**{message.caption or ''}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )

        await asyncio.sleep(0.5)   # gentle rate limit

        if not db_crash:
            try:
                await bot.db.increment_stat("forwarded")
            except Exception as e:
                logger.error(f"❌ stat error: {e}")

        logger.info(f"✅ Copied msg.id={message.id} from chat={message.chat.id}")

    except Exception as e:
        logger.error(f"❌ copy failed msg.id={message.id}: {e}")


async def _worker(bot):
    """Single worker that always takes the lowest message.id first."""
    logger.info("🚀 Ordered forward worker started (priority by message.id)")
    while True:
        try:
            # PriorityQueue item: (message.id, seq, chat, message, db_crash)
            msg_id, seq, chat, message, db_crash = await _priority_queue.get()
            await _process_one(bot, chat, message, db_crash)
            _priority_queue.task_done()
        except asyncio.CancelledError:
            logger.info("🛑 Worker cancelled")
            break
        except Exception as e:
            logger.error(f"❌ Worker crashed: {e}")
            # keep going – one bad item must not kill the queue


def start_forward_worker(bot):
    """Must be called once from UserBot.start()"""
    global _priority_queue, _worker_task
    if _priority_queue is None:
        _priority_queue = asyncio.PriorityQueue()
    if _worker_task is None or _worker_task.done():
        _worker_task = asyncio.create_task(_worker(bot))
        logger.info("✅ Priority forward worker task created")


@Client.on_message(filters.channel & media_filter)
async def forward_media(bot, message):
    try:
        if _priority_queue is None:
            start_forward_worker(bot)

        try:
            chat = await bot.db.get_channel()
        except Exception as e:
            chat = -1001912424642
            logger.error(f"❌ get_channel failed: {e}")

        if not chat or message.chat.id == chat:
            return

        file_unique_id = None
        if message.video:
            file_unique_id = message.video.file_unique_id
        elif message.document:
            file_unique_id = message.document.file_unique_id

        if not file_unique_id:
            return

        # Duplicate check stays parallel (fast path)
        result = None
        db_crash = False
        try:
            result = await bot.db.add_media(file_unique_id)
        except Exception as e:
            db_crash = True
            logger.error(f"❌ add_media failed: {e}")

        if result == "duplicate":
            logger.info(f"🚫 Duplicate {file_unique_id}")
            try:
                await bot.db.increment_stat("duplicates")
            except Exception:
                pass
            return

        # Enqueue with priority = message.id → lowest ID is always processed first
        global _seq
        async with _seq_lock:
            _seq += 1
            seq = _seq

        await _priority_queue.put((message.id, seq, chat, message, db_crash))

    except Exception as e:
        logger.error(f"❌ Handler error: {e}")
