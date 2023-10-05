from pyrogram import Client, enums
from config import LOGGER, Config

class User(Client):
    def __init__(self):
        super().__init__(
            'forwarduserbot',
            api_hash=Config.API_HASH,
            api_id=Config.API_ID,
            workers=8,
            session_string=Config.SESSION
            plugins={'root': 'plugins'}
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.set_parse_mode(enums.ParseMode.HTML)
        self.LOGGER(__name__).info(
            f"User {usr_bot_me.first_name} (@{usr_bot_me.username})  started!"
        )
        return self, usr_bot_me.id

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("User stopped. Bye.")
        
