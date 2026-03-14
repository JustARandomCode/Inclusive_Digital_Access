from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db_instance = Database()


async def connect_to_mongo():
    try:
        db_instance.client = AsyncIOMotorClient(settings.mongo_uri)
        db_instance.db = db_instance.client[settings.mongo_db_name]
        await db_instance.client.admin.command("ping")
        logger.info("Connected to MongoDB")

        # Create indexes at startup — queries on these fields would full-scan otherwise
        await db_instance.db.forms.create_index([("user_id", 1)])
        await db_instance.db.forms.create_index([("form_id", 1)], unique=True)
        await db_instance.db.users.create_index([("username", 1)], unique=True)
        logger.info("MongoDB indexes ensured")

    except Exception as e:
        logger.critical(f"Cannot connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    if db_instance.db is None:
        raise RuntimeError(
            "Database not initialized. "
            "connect_to_mongo() must complete before handling requests."
        )
    return db_instance.db
