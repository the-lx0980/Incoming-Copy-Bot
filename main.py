from pyrogram import Client, filters, enums
from config import Config

media_filter = filters.document | filters.video

Userbot = Client(
  'user-bot',
  api_id=6353248,
  api_hash='1346f958b9d917f0961f3e935329eeee',
  session_string="BQFeVBgAmf0fuR8p_SXLielHmbOFH2VtVyxei4pf0xrJXqHw3hu1fpJg1B2b6GttcGfWVrDtK4d3OPloJtO9iWmwrpZXUsQjmjW7y2tbvb6BFJpmnOK3Z8KhzZqx8tsmFxqe9SczKyenYk9fj6Mkn0LVzL-aKRbRPKvra-YzG0NoJMcRxguFsCXINJWKgFlp9lBFkUORCoI5eDBt5no5cN5wzW70JHrtv17p6xAy-b0xjq4uE_-mmry9WbfhWGtQRe0_A0jjxNz1mIaVwD6mXTZYEkHn_AsIPJ_3ZtOdw5jJV09MVwOkQTnvnYu-2UTkO92ecb688RciX7RmUMKqBFiOV2w0ywAAAAF0GJF_AA"
)

@Userbot.on_message(filters.command('start'))
async def start(bot, update):
    await update.reply("Zinda hain abhi.... 😐")

@Userbot.on_message(filters.chat(Config.FROM_CHAT) & media_filter)
async def forward(bot, update):
    try:
        await bot.copy_message(
            chat_id=Config.TO_CHAT,
            from_chat_id=update.chat.id,
            message_id=update.id,
            caption=f"**{update.caption}**",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    except Exception as e:
        print(e) 

Userbot.run()
