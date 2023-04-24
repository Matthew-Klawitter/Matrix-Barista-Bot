import asyncio
import os

from nio import MatrixRoom, RoomMessageText
from tortoise import Tortoise, run_async

from api.data_objects import Message
from plugins.plugin_loader import PluginLoader

import logging

LOG = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, bridge, user):
        self.bridge = bridge
        self.user = user[1:user.index(":")]
        self.loader = PluginLoader()
        self.plugins = self.loader.plugins
        self.commands = {}
        self.message_listeners = []
        self.should_process_periodically = True
        self.periodic_timeout = 1

    def load_plugins(self, default_room, web_app, web_admin):
        for p in self.plugins:
            LOG.info(f"Loading {p}")
            p.load(default_room, web_app, web_admin)
            for command, callback in p.get_commands().items():
                self.commands[command] = callback
            if hasattr(p, "message_listener"):
                self.message_listeners.append(p.message_listener)

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText) -> None:
        message = Message(self.bridge, room, event)
        if not message.username.lower() == self.user.lower():
            for listener in self.message_listeners:
                try:
                    await listener(message)
                except Exception as e:
                    LOG.error(e)
            if message.is_command and message.command in self.commands:
                await self.commands[message.command](message)

    async def initialize_loop(self):
        asyncio.create_task(self.periodic_loop())

    async def periodic_loop(self):
        while self.should_process_periodically:
            for plugin in self.plugins:
                await plugin.periodic_task()
            await asyncio.sleep(self.periodic_timeout)
