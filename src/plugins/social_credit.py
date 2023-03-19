import logging
import shelve

from aiohttp import web
from plugins.base_plugin import BasePlugin


LOG = logging.getLogger(__name__)


class SocialCreditPlugin(BasePlugin):
    def load(self, room, web_app, web_admin):
        with shelve.open("/data/credit", writeback=True) as data:
            if "credit" not in data:
                data["credit"] = {}
            self.credit = data["credit"]
        self.titles = [
            {"threshold": 0, "title": "Untrustworthy"},
            {"threshold": 20, "title": "Troglodyte"},
            {"threshold": 100, "title": "Goblin-pilled"},
            {"threshold": 200, "title": "Gnome-based"},
            {"threshold": 300, "title": "Trusted"},
            {"threshold": 400, "title": "Proven"},
            {"threshold": 500, "title": "Loyalist"},
        ]

    def unload(self):
        pass

    async def periodic_task(self):
        pass

    async def message_listener(self, message):
        await self.rate_message(message)

        title = self.credit[message.username]["title"]
        score = self.credit[message.username]["score"]
        for i in range(len(self.titles)-1):
            t = self.titles[i]
            nt = self.titles[i+1]
            if t["threshold"] < score and nt["threshold"] >= score and \
                    t["title"] != title:
                with shelve.open("/data/credit", writeback=True) as data:
                    self.credit = data["credit"]
                    self.credit[message.username]["title"] = t["title"]
                    txt = f"{message.username} is now known as '{t['title']}'"
                    await message.bridge.send_message(message.room_id, text=txt)
                    data.sync()

    def add_user(self, username):
        with shelve.open("/data/credit", writeback=True) as data:
            self.credit = data["credit"]
            self.credit[username] = {
                "score": 0,
                "title": "Untrustworthy",
            }
            data.sync()

    def get_commands(self):
        return {"credit": self.get_credit}

    def get_name(self):
        return "Social Credit Monitor"

    def get_help(self):
        return "Please ignore"

    async def rate_message(self, message):
        if message.username not in self.credit:
            self.add_user(message.username)

        msg = message.message.lower()
        changes = []
        if "http://" in msg:
            changes.append({
                "score": -2,
                "reason": "unsecure link",
            })
        if "https://" in msg:
            changes.append({
                "score": 2,
                "reason": "secure link",
            })
        if "reddit.com" in msg:
            changes.append({
                "score": -4,
                "reason": "reddit brained",
            })
        if "twitter.com" in msg:
            changes.append({
                "score": -4,
                "reason": "twitter brained",
            })
        if "!clip" in msg:
            changes.append({
                "score": 4,
                "reason": "soundclip contribution",
            })

        with shelve.open("/data/credit", writeback=True) as data:
            self.credit = data["credit"]
            if changes:
                await message.bridge.send_message(message.room_id,
                    text="\n".join(
                        [f'{x["score"]}: {x["reason"]}' for x in changes]
                    ))
                for change in changes:
                    self.credit[message.username]["score"] += change["score"]
            else:
                self.credit[message.username]["score"] += 1
            data.sync()

    async def get_credit(self, message):
        for k, v in self.credit.items():
            txt = f"{v['title']} {k}, {v['score']}"
            await message.bridge.send_message(message.room_id, text=txt)
