import os

from nio import MatrixRoom, RoomMessageText
from tortoise import Tortoise, run_async

from api.data_objects import Message
from plugins.roll import DicePlugin
from plugins.preview import PreviewPlugin
from plugins.celebrate import CelebratePlugin
from plugins.dad import DadPlugin
from plugins.wiki import WikiPlugin
from plugins.mumble import MumblePlugin
from plugins.ratio import RatioPlugin
from plugins.rip import RipPlugin
from plugins.pin import PinPlugin
from plugins.social_credit import SocialCreditPlugin

import logging

LOG = logging.getLogger(__name__)

PLUGINS = {
    "Celebrate": CelebratePlugin,
    "Dad": DadPlugin,
    "Clippy": MumblePlugin,
    "Preview": PreviewPlugin,
    "Roll": DicePlugin,
    "Wiki": WikiPlugin,
    "Ratio": RatioPlugin,
    "Rip": RipPlugin,
    "Pin": PinPlugin,
    "SocialCredit": SocialCreditPlugin,
}

class PluginManager:
    def __init__(self, bridge, user):
        self.bridge = bridge
        self.user = user[1:user.index(":")]
        config_plugins = os.getenv("PLUGINS").split(",")
        self.plugins = [
            PLUGINS[name]() for name in config_plugins
            if name in PLUGINS
        ]
        self.commands = {}
        self.message_listeners = []
        self.models = []

    async def load_database(self):
        # Load all plugin models first
        for p in self.plugins:
            if p.get_model() is not None:
                for model in p.get_model():
                    self.models.append('plugins.' + model)

        # Build the schema
        LOG.info("Attempting to create database...")
        LOG.info(self.models)
        await self.init_database(self.models)
        LOG.info("Database initialized!")

    def load_plugins(self, default_room, web_app, web_admin):
        for p in self.plugins:
            LOG.info(f"Loading {p}")
            p.load(default_room, web_app, web_admin)
            for command, callback in p.get_commands().items():
                self.commands[command] = callback
            if hasattr(p, "message_listener"):
                self.message_listeners.append(p.message_listener)

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText) -> None:
        message = Message(self.bridge, room, event)
        if not message.username.lower() == self.user.lower():
            for listener in self.message_listeners:
                try:
                    await listener(message)
                except Exception as e:
                    LOG.error(e)
            if message.is_command and message.command in self.commands:
                await self.commands[message.command](message)

    async def init_database(self, models):
        await Tortoise.init(
            db_url='sqlite://db.sqlite3',
            modules={'models': models}
        )
        await Tortoise.generate_schemas()