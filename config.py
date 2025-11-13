from os import getenv
import logging

class Config(object):
    API_ID = int(getenv("API_ID", 0))
    API_HASH = getenv("API_HASH")
    SESSION = getenv("SESSION")
    DB_URL = getenv("DB_URL")
    ADMINS = [int(x) for x in getenv("ADMINS", "0").split(",") if x.strip().isdigit()]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
LOGGER = logging.getLogger("copy-user-bot")

