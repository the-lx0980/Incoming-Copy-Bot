import os, asyncio, logging
from pyrogram import filters, enums
import logging
logger = logging.getLogger(__name__)
from pyrogram import Client, filters



media_filter = filters.document | filters.video

@Client.on_message(media_filter)
async def forward(bot, update):
    try:
        await bot.copy_message(
            chat_id=Config.CHANNEL_ID,
            from_chat_id=update.chat.id,
            message_id=update.id,
            caption=f"**{update.caption}**",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    except FloodWait as e:
        time.sleep(e.x)
