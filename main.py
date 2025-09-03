from pyrogram import Client, filters, enums
from config import Config

media_filter = filters.document | filters.video

Userbot = Client(
  'user-bot',
  api_id=6353248,
  api_hash='1346f958b9d917f0961f3e935329eeee',
  session_string=Config.SESSION
)
  
@Userbot.on_message(filters.command('start'))
async def start(bot, update):
    await update.reply("Zinda hain.... 😐")

@Userbot.on_message(filters.channel & media_filter)
async def forward_group(bot, update):
    try:
        await bot.copy_message(
            chat_id=Config.CHANNEL_ID,
            from_chat_id=update.chat.id,
            message_id=update.id,
            caption=f"**{update.caption}**",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    except Exception as e:
        print(e)

Userbot.run()
