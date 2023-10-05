import os, logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

class Config(object):
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
    SESSION = os.environ.get("SESSION")
    CHANNEL_ID = -1001912424642

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
