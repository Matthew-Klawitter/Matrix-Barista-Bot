from src.plugins.roll import DicePlugin


class PluginManager:
    def __init__(self):
        self.plugins = [DicePlugin()]
        self.command_map = {}

    async def map_commands(self):
        for p in self.plugins:
            commands = await p.get_commands()
            for com in commands:
                self.command_map[com] = p
