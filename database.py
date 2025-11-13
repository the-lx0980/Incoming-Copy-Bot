import logging
from pymongo.mongo_client import AsyncMongoClient
from pymongo import ASCENDING, errors

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_url = db_url
        self.client = None
        self.db = None
        self.collection = None
        self.stats = None

    async def connect(self):
        """Initialize MongoDB connection with auto-reconnect and index"""
        try:
            self.client = AsyncMongoClient(self.db_url, serverSelectionTimeoutMS=5000)
            await self.client.admin.command("ping")
            self.db = self.client["UserbotDB"]
            self.collection = self.db["ForwardedMedia"]
            self.stats = self.db["Stats"]
            await self.collection.create_index([("file_unique_id", ASCENDING)], unique=True)
            logger.info("✅ MongoDB connected successfully.")
        except errors.ServerSelectionTimeoutError as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise e

    async def ensure_connection(self):
        try:
            await self.client.admin.command("ping")
        except Exception:
            logger.warning("⚠️ MongoDB connection lost, reconnecting...")
            await self.connect()

    async def is_duplicate(self, file_unique_id: str) -> bool:
        await self.ensure_connection()
        doc = await self.collection.find_one({"file_unique_id": file_unique_id})
        return doc is not None

    async def add_media(self, file_unique_id: str):
        await self.ensure_connection()
        await self.collection.insert_one({"file_unique_id": file_unique_id})

    async def increment_stat(self, key: str):
        await self.ensure_connection()
        await self.stats.update_one({"_id": "stats"}, {"$inc": {key: 1}}, upsert=True)

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
        
