import os
from pathlib import Path
from api.data_objects import Message

from plugins.base_plugin import BasePlugin

import shelve


class PinPlugin(BasePlugin):
    def load(self, room, web_app, web_admin):
        with shelve.open("/data/pins", writeback=True) as data:
            if "pins" not in data:
                data["pins"] = []

    def unload(self):
        pass

    async def periodic_task(self, bridge):
        pass

    async def message_listener(self, message):
        pass

    def get_commands(self):
        return {"pin": self.pin, "pins": self.pins}

    def get_name(self):
        return "Roll"

    def get_help(self):
        return "/pin or /pins"

    async def pin(self, message):
        if message.is_reply:
            with shelve.open("/data/pins", writeback=True) as data:
                data["pins"].append(message.replied_message)
                data.sync()
                await message.bridge.send_message(message.room_id, text="Pinned message.")

    async def pins(self, message):
        with shelve.open("/data/pins", writeback=True) as data:
            if not data["pins"]:
                await message.bridge.send_message(message.room_id, text="No pinned messages")
            for pin in data["pins"]:
                await message.bridge.send_message(message.room_id, text=pin)
