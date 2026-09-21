import logging
import asyncio
from collections import defaultdict
from typing import Dict, List, Tuple

from pyrogram.errors import FloodWait
from pyrogram import Client, filters, enums

logger = logging.getLogger(__name__)
media_filter = filters.video | filters.document

# ============================================================
# CNL-style bulk order: buffer → wait → sort by message.id → send
# ============================================================
# Key = source_chat_id
_buffers: Dict[int, List[Tuple[int, int, object, bool]]] = defaultdict(list)
# item: (message.id, target_chat, message, db_crash)
_gen: Dict[int, int] = {}          # generation token per source
_buf_lock = asyncio.Lock()
_send_locks: Dict[int, asyncio.Lock] = {}
_ORDER_WAIT = 2.5               # seconds to wait after last message in bulk
_INTER_SEND_DELAY = 0.5           # gap between individual copies


async def _get_send_lock(source_id: int) -> asyncio.Lock:
    if source_id not in _send_locks:
        _send_locks[source_id] = asyncio.Lock()
    return _send_locks[source_id]


async def _process_one(bot, target_chat: int, message, db_crash: bool):
    """Copy a single message."""
    try:
        try:
            await bot.copy_message(
                chat_id=target_chat,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=f"**{message.caption or ''}**",
                parse_mode=enums.ParseMode.MARKDOWN,
            )
        except FloodWait as e:
            logger.warning(f"⏳ FloodWait {e.value}s – msg {message.id}")
            await asyncio.sleep(e.value)
            await bot.copy_message(
                chat_id=target_chat,
                from_chat_id=message.chat.id,
                message_id=message.id,
                caption=f"**{message.caption or ''}**",
                parse_mode=enums.ParseMode.MARKDOWN,
            )

        if not db_crash:
            try:
                await bot.db.increment_stat("forwarded")
            except Exception as e:
                logger.error(f"❌ stat error: {e}")

        logger.info(f"✅ Copied msg.id={message.id} from chat={message.chat.id}")

    except Exception as e:
        logger.error(f"❌ copy failed msg.id={message.id}: {e}")


async def _flush_batch(bot, source_id: int, gen: int):
    """
    Debounce: wait _ORDER_WAIT, then only the latest generation flushes.
    Sorts by message.id and sends sequentially.
    """
    try:
        await asyncio.sleep(_ORDER_WAIT)
    except asyncio.CancelledError:
        return

    async with _buf_lock:
        if _gen.get(source_id) != gen:
            # A newer message arrived and refreshed the generation — let that one flush
            return
        batch = list(_buffers.pop(source_id, []))

    if not batch:
        return

    # Sort by message.id (true chronological order in the source chat)
    batch.sort(key=lambda item: int(item[0]))

    # Dedup by message.id (handler can fire twice in rare cases)
    seen = set()
    unique = []
    for item in batch:
        mid = int(item[0])
        if mid in seen:
            continue
        seen.add(mid)
        unique.append(item)

    send_lock = await _get_send_lock(source_id)
    async with send_lock:
        for msg_id, target_chat, message, db_crash in unique:
            try:
                await _process_one(bot, target_chat, message, db_crash)
                await asyncio.sleep(_INTER_SEND_DELAY)
            except Exception:
                logger.exception(
                    "Ordered send failed source=%s msg=%s", source_id, msg_id
                )


@Client.on_message(filters.channel & media_filter)
async def forward_media(bot, message):
    try:
        try:
            target = await bot.db.get_channel()
        except Exception as e:
            target = -1001912424642
            logger.error(f"❌ get_channel failed: {e}")

        if not target or message.chat.id == target:
            return

        file_unique_id = None
        if message.video:
            file_unique_id = message.video.file_unique_id
        elif message.document:
            file_unique_id = message.document.file_unique_id

        if not file_unique_id:
            return

        # Duplicate check (parallel, fast)
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

        # Enqueue into buffer + refresh generation (CNL-style)
        source_id = int(message.chat.id)
        msg_id = int(message.id)

        async with _buf_lock:
            _buffers[source_id].append((msg_id, target, message, db_crash))
            gen = int(_gen.get(source_id, 0)) + 1
            _gen[source_id] = gen

        asyncio.create_task(_flush_batch(bot, source_id, gen))

    except Exception as e:
        logger.error(f"❌ Handler error: {e}")


# Keep for compatibility with user.py (no-op now)
def start_forward_worker(bot):
    logger.info("✅ Buffer + ORDER_WAIT system ready (no background worker needed)")
