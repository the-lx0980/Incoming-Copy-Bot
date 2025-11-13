import logging
from pyrogram import filters, enums

logger = logging.getLogger(__name__)
media_filter = filters.video | filters.document


@Client.on_message(filters.channel & media_filter)
async def forward_media(bot, message):
    """
    Forwards new media from source channel → target channel.
    Prevents duplicate forwarding by checking file_unique_id in DB.
    """
    try:
        file_unique_id = None
        if message.video:
            file_unique_id = message.video.file_unique_id
        elif message.document:
            file_unique_id = message.document.file_unique_id

        if not file_unique_id:
            return

        if await bot.db.is_duplicate(file_unique_id):
            await bot.db.increment_stat("duplicates")
            logger.info(f"🚫 Duplicate skipped: {file_unique_id}")
            return

        chat = await bot.db.get_channel()
        if not chat:
            return
        await bot.copy_message(
            chat_id=chat,
            from_chat_id=message.chat.id,
            message_id=message.id,
            caption=f"**{message.caption or ''}**",
            parse_mode=enums.ParseMode.MARKDOWN
        )

        await bot.db.add_media(file_unique_id)
        await bot.db.increment_stat("forwarded")

    except Exception as e:
        logger.error(f"❌ Forwarding failed: {e}")
