import logging
from pyrogram import Client, __version__, enums
from config import Config
from database import Database  

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
LOGGER = logging.getLogger("copy-user-bot")


class UserBot(Client):
    def __init__(self):
        super().__init__(
            "userClient",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            plugins={"root": "plugins"},
            workers=20,
            session_string=Config.SESSION,
            sleep_threshold=10
        )
        self.LOGGER = LOGGER
        self.db = Database()  # ✅ Database instance

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        self.set_parse_mode(enums.ParseMode.HTML)
        bot = await self.get_me()

        try:
            await self.db.connect()
            self.LOGGER.info("📦 Database connected successfully.")
        except Exception as e:
            self.LOGGER.error(f"❌ Database connection failed: {e}")
            raise

        self.LOGGER.info(f"🤖 Userbot started as @{bot.username} (ID: {bot.id})")
        self.LOGGER.info(f"Pyrogram v{__version__} is running...")

    async def stop(self, *args, **kwargs):
        await self.db.close()
        await super().stop(*args, **kwargs)
        self.LOGGER.info("🛑 Userbot stopped. Goodbye!")
