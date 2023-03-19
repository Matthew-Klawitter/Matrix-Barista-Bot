import logging
import re, os, random

from aiohttp import web
from plugins.base_plugin import BasePlugin


LOG = logging.getLogger(__name__)


class RipPlugin(BasePlugin):
    def load(self, room, web_app, web_admin):
        pass

    def unload(self):
        pass

    async def periodic_task(self):
        pass

    async def message_listener(self, message):
        msg = message.message.lower()
        if re.search(r"\brip\b", msg):
            try:
                files = os.listdir("/res/rip")
                filename = "/res/rip/" + random.choice(files)
                await message.bridge.send_image(message.room_id, filename)
            except:
                pass

    def get_commands(self):
        return {}

    def get_name(self):
        return "Rip"

    def get_help(self):
        return "Responds to messages with 'rip'\n"
