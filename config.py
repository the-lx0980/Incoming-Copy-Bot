from os import getenv
import logging

class Config(object):
    API_ID = int(getenv("API_ID", 0))
    API_HASH = getenv("API_HASH")
    SESSION = getenv("SESSION")
    DB_URL = getenv("DB_URL")
    ADMINS = [int(x) for x in getenv("ADMINS", "0").split(",") if x.strip().isdigit()]

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
