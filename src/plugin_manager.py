from nio import MatrixRoom, RoomMessageText

from api.data_objects import Message
from plugins.roll import DicePlugin
from plugins.preview import PreviewPlugin
from plugins.celebrate import CelebratePlugin

import logging

LOG = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, bridge):
        self.bridge = bridge
        self.plugins = [DicePlugin(), PreviewPlugin(), CelebratePlugin()]
        self.commands = {}
        self.message_listeners = []
        for p in self.plugins:
            for command, callback in p.get_commands().items():
                self.commands[command] = callback
            if hasattr(p, "message_listener"):
                self.message_listeners.append(p.message_listener)

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText) -> None:
        message = Message(self.bridge, room, event)
        for listener in self.message_listeners:
            try:
                await listener(message)
            except Exception as e:
                LOG.error(e)
        if message.is_command and message.command in self.commands:
            await self.commands[message.command](message)
