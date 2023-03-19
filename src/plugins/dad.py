import logging

from aiohttp import web
from plugins.base_plugin import BasePlugin


LOG = logging.getLogger(__name__)

class DadPlugin(BasePlugin):
    def load(self, room, web_app, web_admin):
        pass

    def unload(self):
        pass

    async def periodic_task(self):
        pass

    def message_listener(self, message):
        pass

    def get_commands(self):
        return {}

    def get_name(self):
        return "Dad"

    def get_help(self):
        return "Responds to instances of 'I'm'\n"

    async def message_listener(self, message):
        msg = message.message.lower()
        if msg.startswith("i'm ") or msg.startswith("im "):
            await message.bridge.send_message(message.room_id, text="Hi {}, I'm dad!".format(msg[3:].strip()))
