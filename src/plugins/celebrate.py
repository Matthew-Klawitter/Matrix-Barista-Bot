import heapq
import bs4 as bs
import re
import urllib.request
import nltk
nltk.download('punkt')
nltk.download('stopwords')

import requests
from lxml.html import fromstring
from aiohttp import web

import logging

LOG = logging.getLogger(__name__)

class CelebratePlugin:
    def load(self, room, web_app, web_admin):
        pass

    def get_commands(self):
        return {}

    def get_name(self):
        return "Celebrate"

    def get_help(self):
        return "Sends a fireworks\n"

    async def message_listener(self, message):
        if (re.search(r'\bwow\b', message.message, flags=re.IGNORECASE) or
                re.search(r'\bnice\b', message.message, flags=re.IGNORECASE) or
                re.search(r'\bawesome\b', message.message, flags=re.IGNORECASE) or
                re.search(r'\bcongrats\b', message.message, flags=re.IGNORECASE)):
            await message.bridge.send_message(message.room_id, text="wow!", msg_type="nic.custom.fireworks")
