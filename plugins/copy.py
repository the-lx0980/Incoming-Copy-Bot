import logging
from pyrogram import Client, filters, enums

logger = logging.getLogger(__name__)
media_filter = filters.video | filters.document

@Client.on_message(filters.channel & media_filter)
async def forward_media(bot, message):
    try:
        # Extract unique file ID
        file_unique_id = (
            message.video.file_unique_id if message.video else
            message.document.file_unique_id if message.document else
            None
        )

        if not file_unique_id:
            return

        # 🔥 ATOMIC duplicate check (no race condition)
        is_new = await bot.db.add_media(file_unique_id)

        if not is_new:
            await bot.db.increment_stat("duplicates")
            logger.info(f"🚫 Duplicate skipped: {file_unique_id}")
            return

        # Fetch target channel
        chat = await bot.db.get_channel()
        if not chat:
            return

        # Forward media
        await bot.copy_message(
            chat_id=chat,
            from_chat_id=message.chat.id,
            message_id=message.id,
            caption=f"**{message.caption or ''}**",
            parse_mode=enums.ParseMode.MARKDOWN
        )

        await bot.db.increment_stat("forwarded")

    except Exception as e:
        logger.error(f"❌ Forwarding failed: {e}")
