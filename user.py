import logging
from pyrogram import Client, __version__, enums
from config import Config, LOGGER
from database import Database
from plugins.copy import start_forward_worker

class UserBot(Client):
    def __init__(self):
        super().__init__(
            "userClient",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            plugins={"root": "plugins"},
            workers=8,                 # reduced – actual copying is now sequential
            session_string=Config.SESSION,
            sleep_threshold=10
        )
        self.LOGGER = LOGGER
        self.db = Database()

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

        # Start the sequential forward worker
        start_forward_worker(self)
        self.LOGGER.info("🚀 Sequential forward worker started")

        self.LOGGER.info(f"🤖 Userbot started as @{bot.username} (ID: {bot.id})")
        self.LOGGER.info(f"Pyrogram v{__version__} is running...")

    async def stop(self, *args, **kwargs):
        await self.db.close()
        await super().stop(*args, **kwargs)
        self.LOGGER.info("🛑 Userbot stopped. Goodbye!")
