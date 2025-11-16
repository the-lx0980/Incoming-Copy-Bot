import logging
from pymongo.asyncio import MongoClient
from pymongo import ASCENDING, errors
from config import Config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_url = Config.DB_URL
        self.client = None
        self.db = None
        self.collection = None
        self.stats = None
        self.settings = None
        self._cached_channel = None  # ⚡ in-memory cache for fast get_channel

    async def connect(self):
        """Initialize MongoDB connection with auto-reconnect and index"""
        try:
            self.client = MongoClient(
                self.db_url,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=30,
                minPoolSize=5,
                connectTimeoutMS=4000,
            )
            await self.client.admin.command("ping")

            self.db = self.client["UserbotDB"]
            self.collection = self.db["ForwardedMedia"]
            self.stats = self.db["Stats"]
            self.settings = self.db["Settings"]

            await self.collection.create_index(
                [("file_unique_id", ASCENDING)], unique=True
            )

            doc = await self.settings.find_one({"_id": "to_channel"})
            self._cached_channel = doc.get("channel_id") if doc else None

            logger.info("✅ MongoDB connected successfully.")
        except errors.ServerSelectionTimeoutError as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise e

    async def ensure_connection(self):
        """Verify connection; reconnect if lost"""
        if not self.client:
            await self.connect()
            return
        try:
            await self.client.admin.command("ping")
        except Exception:
            logger.warning("⚠️ MongoDB connection lost — reconnecting...")
            await self.connect()

    async def is_duplicate(self, file_unique_id: str) -> bool:
        await self.ensure_connection()
        count = await self.collection.count_documents({"file_unique_id": file_unique_id}, limit=1)
        return count > 0

    async def add_media(self, file_unique_id: str):
        await self.ensure_connection()
        try:
            await self.collection.insert_one({"file_unique_id": file_unique_id})
        except errors.DuplicateKeyError:
            logger.debug(f"Duplicate ignored: {file_unique_id}")

    async def increment_stat(self, key: str):
        await self.ensure_connection()
        await self.stats.update_one(
            {"_id": "stats"},
            {"$inc": {key: 1}},
            upsert=True
        )

    async def get_stats(self) -> dict:
        await self.ensure_connection()
        stats = await self.stats.find_one({"_id": "stats"}) or {}
        forwarded = stats.get("forwarded", 0)
        duplicates = stats.get("duplicates", 0)
        total = await self.collection.estimated_document_count()
        return {"forwarded": forwarded, "duplicates": duplicates, "total": total}

    async def clear_all(self):
        await self.ensure_connection()
        await self.collection.delete_many({})
        await self.stats.delete_many({})
        logger.info("🧹 Database cleared.")

    async def set_channel(self, channel_id: int):
        """Save the forward target channel (only one allowed)"""
        await self.ensure_connection()
        await self.settings.update_one(
            {"_id": "to_channel"},
            {"$set": {"channel_id": channel_id}},
            upsert=True
        )
        self._cached_channel = channel_id
        logger.info(f"✅ Forward channel set to {channel_id}")

    async def get_channel(self) -> int | None:
        """Return saved forward channel — uses in-memory cache (O(1))"""
        # ⚡ Instant return if cached
        if self._cached_channel is not None:
            return self._cached_channel
        # fallback (if cache empty)
        await self.ensure_connection()
        doc = await self.settings.find_one({"_id": "to_channel"})
        self._cached_channel = doc.get("channel_id") if doc else None
        return self._cached_channel

    async def delete_channel(self):
        await self.ensure_connection()
        await self.settings.delete_one({"_id": "to_channel"})
        self._cached_channel = None  # clear cache
        logger.info("🗑️ Forward channel removed.")

    async def close(self):
        if self.client:
            await self.client.close()
            logger.info("🔌 MongoDB connection closed.")
