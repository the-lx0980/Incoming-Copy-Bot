import logging
from pymongo import AsyncMongoClient
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
        self._cached_channel = None  # ⚡ Fast in-memory cache

    async def connect(self):
        """Initialize MongoDB connection with auto-reconnect and index"""
        try:
            self.client = AsyncMongoClient(
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

            # ⚡ atomic duplicate protection
            await self.collection.create_index("_id", unique=True)

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

    # ❌ REMOVED is_duplicate() — no longer needed
    # Duplicate check is now atomic inside add_media()

    async def add_media(self, file_unique_id: str) -> bool:
        """
        Insert media atomically.
        Returns:
            True  → new file (not duplicate)
            False → duplicate
        """
        await self.ensure_connection()
        try:
            await self.collection.insert_one({"_id": file_unique_id})
            return True
        except errors.DuplicateKeyError:
            return False

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
        return {
            "forwarded": forwarded,
            "duplicates": duplicates,
            "total": total
        }

    async def clear_all(self):
        await self.ensure_connection()
        await self.collection.delete_many({})
        await self.stats.delete_many({})
        logger.info("🧹 Database cleared.")

    async def set_channel(self, channel_id: int):
        """Save the forward target channel"""
        await self.ensure_connection()
        await self.settings.update_one(
            {"_id": "to_channel"},
            {"$set": {"channel_id": channel_id}},
            upsert=True
        )
        self._cached_channel = channel_id
        logger.info(f"✅ Forward channel set to {channel_id}")

    async def get_channel(self) -> int | None:
        """Return saved forward channel — with fast cache"""
        if self._cached_channel is not None:
            return self._cached_channel

        await self.ensure_connection()
        doc = await self.settings.find_one({"_id": "to_channel"})
        self._cached_channel = doc.get("channel_id") if doc else None
        return self._cached_channel

    async def delete_channel(self):
        await self.ensure_connection()
        await self.settings.delete_one({"_id": "to_channel"})
        self._cached_channel = None
        logger.info("🗑️ Forward channel removed.")

    async def close(self):
        if self.client:
            await self.client.close()
            logger.info("🔌 MongoDB connection closed.")
