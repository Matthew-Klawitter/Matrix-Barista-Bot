import random
import re


"""
Main Plugin class that manages command usage
"""

class AnonPlugin:
    def load(self, room):
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
