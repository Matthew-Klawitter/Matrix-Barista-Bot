from nio import MatrixRoom, RoomMessageText

from src.api.data_objects import Command
from src.plugins.roll import DicePlugin


class PluginManager:
    def __init__(self, bridge):
        self.bridge = bridge
        self.plugins = [DicePlugin()]
        self.command_map = {}

    async def map_commands(self):
        for p in self.plugins:
            commands = await p.get_commands()
            for com in commands:
                self.command_map[com] = p

    async def message(self, room: MatrixRoom, event: RoomMessageText) -> None:
        prefix = event.body.split(" ")[0]
        msg = event.body.split(' ', 1)[1]
        command = Command(self.bridge, prefix, room.user_name(event.sender), room.room_id, room.display_name, msg)

        print(prefix)

        try:
            await self.command_map[prefix].task(command)
        except KeyError:
            pass
