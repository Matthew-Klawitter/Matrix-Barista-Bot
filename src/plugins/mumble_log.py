import datetime
import logging
import os
import re

LOG = logging.getLogger(__name__)

class MumbleAlerts:
    def __init__(self):
        self.room = None
        self.last_update = None
        self.pattern = re.compile(r"...(\d.+ .+) 1 => <.+:(.+)\(.+\).+")

    def load(self, room, web_app, web_admin):
        self.room = room
        pass

    def unload(self):
        pass

    async def periodic_task(self, bridge):
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
                                    elif "Connection closed" in line:
                                        action = "disconnected from"
                                    else:
                                        continue
                                    await bridge.send_message(self.room, text=f"{name} {action} mumble.")
        except FileNotFoundError:
            pass
        except Exception as e:
            LOG.error(e)

    async def message_listener(self, message):
        pass

    def get_commands(self):
        return {}

    def get_name(self):
        return "MumbleLog"

    def get_help(self):
        return "Automatically alerts when a user joins a mumble server"

    def format_date_str(self, stng):
        f = "%Y-%m-%d %H:%M:%S.%f"
        return datetime.datetime.strptime(stng, f)

