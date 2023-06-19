import os, logging

class Config(object):
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
    SESSION = os.environ.get("SESSION")
    CHANNEL_ID = -1001912424642

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
