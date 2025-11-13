import logging
from pyrogram import Client, __version__, enums
from config import API_ID, API_HASH, SESSION
from database import Database  # ✅ Import the database class

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
LOGGER = logging.getLogger("CNL-Auto-Post-Bot")


class UserBot(Client):
    def __init__(self):
        super().__init__(
            "userClient",
            api_hash=API_HASH,
            api_id=API_ID,
            plugins={"root": "plugins"},
            workers=20,
            session_string=SESSION,
            sleep_threshold=10
        )
        self.LOGGER = LOGGER
        self.db = Database()  # ✅ Database instance

    async def start(self, *args, **kwargs):
        """Start bot and connect database."""
        await super().start(*args, **kwargs)
        bot_details = await self.get_me()
        self.set_parse_mode(enums.ParseMode.HTML)

        # ✅ Connect database
        try:
            await self.db.connect()
        except Exception as e:
            self.LOGGER.error(f"❌ Failed to connect to MongoDB: {e}")
            raise SystemExit("Database connection failed. Exiting...")

        self.LOGGER.info(f"🤖 @{bot_details.username} (Pyrogram v{__version__}) started successfully!")
        self.LOGGER.info("📦 MongoDB connection established and ready.")

    async def stop(self, *args, **kwargs):
        """Stop bot and close database connection."""
        try:
            await self.db.close()  # ✅ Close DB cleanly
        except Exception as e:
            self.LOGGER.warning(f"⚠️ Error closing MongoDB: {e}")

        await super().stop(*args, **kwargs)
        self.LOGGER.info("🛑 Bot stopped and MongoDB connection closed.")
