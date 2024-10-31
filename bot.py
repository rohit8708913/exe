from aiohttp import web
from plugins import web_server

import pyromod.listen
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime

from config import (
    API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS,
    FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL2, CHANNEL_ID, CHANNEL_ID2, PORT
)

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()

        # Setup force subscription channels
        self.invitelink = await self.get_or_create_invite(FORCE_SUB_CHANNEL, "FORCE_SUB_CHANNEL")
        self.invitelink2 = await self.get_or_create_invite(FORCE_SUB_CHANNEL2, "FORCE_SUB_CHANNEL2")

        # Setup database channels
        self.db_channel = await self.get_db_channel(CHANNEL_ID, "CHANNEL_ID")
        self.db_channel2 = await self.get_db_channel(CHANNEL_ID2, "CHANNEL_ID2")

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info(f"Bot running as @{usr_bot_me.username}")

        # Web response
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")

    async def get_or_create_invite(self, channel_id, channel_name):
        """Retrieve or create an invite link for a channel."""
        try:
            chat = await self.get_chat(channel_id)
            link = chat.invite_link or await self.export_chat_invite_link(channel_id)
            return link
        except Exception as e:
            self.LOGGER(__name__).warning(f"Error in {channel_name}: {e}")
            self.LOGGER(__name__).info("Bot stopped.")
            sys.exit()

    async def get_db_channel(self, channel_id, channel_name):
        """Ensure bot is admin in the database channel."""
        try:
            db_channel = await self.get_chat(channel_id)
            test_msg = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test_msg.delete()
            return db_channel
        except Exception as e:
            self.LOGGER(__name__).warning(f"Error in {channel_name}: {e}")
            self.LOGGER(__name__).info("Bot stopped.")
            sys.exit()