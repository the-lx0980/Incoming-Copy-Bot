from os import getenv, environ
import re
import logging

id_pattern = re.compile(r'^.\d+$')

class Config(object):
    API_ID = int(getenv("API_ID", 0))
    API_HASH = getenv("API_HASH")
    SESSION = getenv("SESSION")
    FROM_CHAT = [int(ch) if id_pattern.search(ch) else ch for ch in environ['FROM_CHAT'].split()]
    TO_CHAT = int(getenv("TO_CHAT"))

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
