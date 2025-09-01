from pyrogram import Client, filters, enums
from config import Config
import re

media_filter = filters.document | filters.video
SAVR_LOGIN = {}

Userbot = Client(
  'user-bot',
  api_id=6353248,
  api_hash='1346f958b9d917f0961f3e935329eeee',
  session_string=Config.SESSION
)
  

@Userbot.on_message(filters.command('start'))
async def start(bot, update):
    await update.reply("Zinda hain.... 😐")
    user = await bot.get_me()
    await update.reply(user)

@Userbot.on_message(filters.command("send")) #, prefixes="!"))  # !send likhne par trigger hoga
async def send_code(client, message):
    global SAVR_LOGIN
    if "code" in SAVR_LOGIN:
        code = SAVR_LOGIN["code"]
        formatted = " ".join(code)  # 2 4 7 6 3
        chat_id = -100123456897     # apna group/channel id
        text = f"({formatted})")
        message.reply(f"Here is the code {text}")
    else:
        message.reply("❌ Abhi koi login code saved nahi hai.")
  

@Userbot.on_message(filters.private & filters.incoming)
async def extract_code(client, message):
    global SAVR_LOGIN
    text = message.text or ""

    # Regex: 5-digit code find karega
    match = re.search(r"\b\d{5}\b", text)
    if match:
        code = match.group(0)
        SAVR_LOGIN["code"] = code

ABC = """
@Userbot.on_message() #filters.channel & media_filter)
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
        print(e) 

ABC = @Userbot.on_message(filters.group & media_filter)
async def forward_group(bot, update):
    try:
        await bot.copy_message(
            chat_id=-1002082734364,
            from_chat_id=update.chat.id,
            message_id=update.id,
            caption=f"**{update.caption}**",
            parse_mode=enums.ParseMode.MARKDOWN
        )
    except Exception as e:
        print(e)"""

Userbot.run()
