import random
import re
import requests
from lxml.html import fromstring

class PreviewPlugin:
    def get_commands(self):
        return {}

    def get_name(self):
        return "Preview"

    def get_help(self):
        return "Sends a preview of a link\n"

    async def message_listener(self, message):
        urls = re.findall(r'(https?://\S+)', message.message)
        for url in urls:
            r = requests.get(url)
            tree = fromstring(r.content)
            title = tree.findtext('.//title')
            await message.bridge.send_message(message.room_id, title)
