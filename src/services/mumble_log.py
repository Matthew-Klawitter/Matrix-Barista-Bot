import datetime
import os
import shelve

import re
import logging

LOG = logging.getLogger(__name__)

class MumbleAlerts:
    def __init__(self, bridge, room):
        self.bridge = bridge
        self.room = room
        self.last_update = None
        self.pattern = re.compile(r"...(\d.+ .+) 1 => <.+:(.+)\(.+\).+")
        self.map = {}
        with open("/res/mumble_map.txt") as f:
            for line in f.readlines():
                parts = line.split(" ")
                self.map[parts[0]] = parts[1]
        self.current_mumble_users = set()

    async def task(self):
        try:
            if os.getenv("MUMBLE_LOG_ENABLED") == "enabled":
                with open("/var/log/mumble-server/mumble-server.log") as f:
                    if not self.last_update:
                        date_str = f.readlines()[-1][3:len("2021-09-22 19:44:16.205")+3]
                        self.last_update = self.format_date_str(date_str)
                    else:
                        for line in f.readlines():
                            m = self.pattern.match(line)
                            if m:
                                date = self.format_date_str(m[1])
                                if date > self.last_update:
                                    self.last_update = date
                                    name = m[2]
                                    if "Authenticated" in line:
                                        action = "connected to"
                                        if name in self.map:
                                            self.current_mumble_users.add(name)
                                        if len(self.current_mumble_users) == 1:
                                            await self.give_credit(name)
                                    elif "Connection closed" in line:
                                        action = "disconnected from"
                                    else:
                                        continue
                                    await self.bridge.send_message(self.room, text=f"{name} {action} mumble.")

        except FileNotFoundError:
            pass
        except Exception as e:
            LOG.error(e)

    def format_date_str(self, stng):
        f = "%Y-%m-%d %H:%M:%S.%f"
        return datetime.datetime.strptime(stng, f)

    async def give_credit(self, mumble_username):
        username = self.map[mumble_username]
        with shelve.open("/data/credit", writeback=True) as data:
            self.credit = data["credit"]
            self.credit[username]["score"] += 30
            await self.bridge.send_message(self.room, text=f"+30 points to {username} for first on mumble")
