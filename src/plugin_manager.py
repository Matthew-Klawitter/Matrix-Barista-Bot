from nio import MatrixRoom, RoomMessageText

from api.data_objects import Message
from plugins.roll import DicePlugin
from plugins.preview import PreviewPlugin


class PluginManager:
    def __init__(self, bridge):
        self.bridge = bridge
        self.plugins = [DicePlugin(), PreviewPlugin()]
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
            await listener(message)
        if message.is_command and message.command in self.commands:
            await self.commands[message.command](message)
