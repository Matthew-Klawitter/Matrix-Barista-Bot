from mcstatus import MinecraftServer

import logging

LOG = logging.getLogger(__name__)

class MCAlerts:
    def __init__(self, bridge, room):
        self.bridge = bridge
        self.room = room
        self.players = 0
        self.server = MinecraftServer("mc.seafarers.cafe", 25565)

    async def task(self):
        try:
            status = self.server.status()

            if status.players.sample is not None:
                if not len(status.players.sample) == self.players:
                    self.players = len(status.players.sample)
                    message = "Minecraft Server - connected users:\n"

                    for p in status.players.sample:
                        message += "{}, ".format(p.name)

                    await self.bridge.send_message(self.room, message)
            else:
                if self.players > 0:
                    self.players = 0
                    await self.bridge.send_message(self.room, "Minecraft Server - no connected users detected.")
        except Exception as e:
            LOG.error(e)
