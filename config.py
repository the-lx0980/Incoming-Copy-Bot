from os import getenv
import logging

class Config(object):
    API_ID = int(getenv("API_ID", 0))
    API_HASH = getenv("API_HASH")
    SESSION = getenv("SESSION")
    CHANNEL_ID = int(getenv("CHANNEL_ID"))

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
