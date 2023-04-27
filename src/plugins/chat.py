import re, os, random

from asyncio import run

async def random_file(parent, message):
    files = os.listdir(parent)
    await message.bridge.send_image(message.room_id, parent + random.choice(files))

async def random_rip(message):
    await random_file("/res/rip/", message)

async def no(message):
    await message.bridge.send_image(message.room_id, "/res/no.jpeg")

responses = (
    ( r"\brip\b", [random_rip] ),
    ( r"no\s\w+\?", [no] ),
)

class ChatPlugin:
    def load(self, room, web_app, web_admin):
        pass

    def get_commands(self):
        return {}

    def get_name(self):
        return "General Chat"

    def get_help(self):
        return "Responds to messages\n"

    async def message_listener(self, message):
        if message.is_command:
            return

        msg = message.message.lower()
        for pattern, callbacks in responses:
            if re.search(pattern, msg, flags=re.IGNORECASE):
                try:
                    random_callback = random.choice(callbacks)
                    await random_callback(message)
                except Exception as e:
                    pass
