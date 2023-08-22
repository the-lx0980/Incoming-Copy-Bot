from pyrogram import filters, Client, enums

import logging
logger = logging.getLogger(__name__)
from config import Config

@Client.on_message(filters.command('start') & filters.private)
async def start(bot, update):
    await update.reply('Zinda hain.... 😐')

@Client.on_message(filters.document | filters.video)
async def forward(bot, update):
    try:
        await bot.copy_message(
            chat_id=Config.CHANNEL_ID,
            from_chat_id=update.chat.id,
            message_id=update.id,
            caption=f"**{update.caption}**",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.exception(e)
