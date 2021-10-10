from mcstatus import MinecraftServer


class MCAlerts:
    def __init__(self, bridge, room):
        self.bridge = bridge
        self.room = room
        self.players = {}
        self.server = MinecraftServer("localhost", 25565)

    async def task(self):
        status = self.server.status()

        # TODO: Solve race condition if multiple players connect/disconnect within same ping period
        if not len(status.players.sample) == len(self.players):
            if len(status.players.sample) > len(self.players):
                message = "The following players connected:\n"
                for p in status.players.sample:
                    if p not in self.players:
                        message += "{}\n".format(p.name)
                self.players = status.players.sample
                await self.bridge.send_message(self.room, message)
            else:
                message = "The following players disconnected:\n"
                for p in self.players:
                    if p not in status.players.sample:
                        message += "{}\n".format(p.name)
                self.players = status.players.sample
                await self.bridge.send_message(self.room, message)
