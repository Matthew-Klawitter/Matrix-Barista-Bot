import requests

import logging

from aiohttp import web

LOG = logging.getLogger(__name__)


"""
Main Plugin class that manages command usage
"""


class WikiPlugin:
    def load(self, room, web_app, web_admin):
        pass

    async def task(self, message):
        if (message.command == "wiki"):
            await message.bridge.send_message(message.room_id, text="https://en.wikipedia.org/wiki/{}".format(message.args.replace(" ", "_")))
        elif (message.command == "wikirand"):
            url = self.get_random()
            await message.bridge.send_message(message.room_id, text=url)

    def get_commands(self):
        return {"wiki": self.task, "wikirand": self.task}

    def get_name(self):
        return "Wiki"

    def get_help(self):
        return "/wiki <term>\n/wikirand\n"

    def get_random(self):
        try:
            response = requests.get("https://en.wikipedia.org/wiki/Special:Random")
            return response.url
        except Exception as e:
            LOG.error(e)
