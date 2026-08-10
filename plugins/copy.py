import logging
import asyncio
from pyrogram.errors import FloodWait
from pyrogram import Client, filters, enums

logger = logging.getLogger(__name__)
media_filter = filters.video | filters.document

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
        file_id = None
        
        if message.video:
            file_unique_id = message.video.file_unique_id
            file_id = message.video.file_id
        elif message.document:
            file_unique_id = message.document.file_unique_id
            file_id = message.document.file_id

        if not file_unique_id or not file_id:
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
            
        try:    
            await bot.send_cached_media(
                chat_id=chat,
                file_id=file_id,
                caption=f"**{message.caption or ''}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        except FloodWait as e:
            logger.warning(f"⏳ FloodWait triggered. Sleeping for {e.value} seconds.")
            await asyncio.sleep(e.value)
            await bot.send_cached_media(
                chat_id=chat,
                file_id=file_id,
                caption=f"**{message.caption or ''}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )   
            
        await asyncio.sleep(1)
        if not db_crash:
            try:
                await bot.db.increment_stat("forwarded")
            except Exception as e:
                logger.error(f"❌ Forwarded Increment Error: {e}")
                
    except Exception as e:
        logger.error(f"❌ Forwarding core pipeline failed: {e}")
