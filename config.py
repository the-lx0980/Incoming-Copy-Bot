from os import getenv

class Config(object):
    BOT_TOKEN = getenv("BOT_TOKEN", "")
    APP_ID = int(getenv("API_ID", 0))
    API_HASH = getenv("API_HASH")
    CHANNEL_ID = int(getenv("CHANNEL_ID"))
