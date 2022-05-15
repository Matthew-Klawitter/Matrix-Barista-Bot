import random
import re

from aiohttp import web

"""
Main Plugin class that manages command usage
"""

class AnonPlugin:
    def load(self, room, web_app, web_admin):
        self.room = room

    async def task(self, message):
        text=f"Message from Anonymous: {message.args}"
        await message.bridge.send_message(self.room, text=text)

    def get_commands(self):
        return {"anon": self.task}

    def get_name(self):
        return "Anonymous"

    def get_help(self):
        return "/anon <message>\n"
