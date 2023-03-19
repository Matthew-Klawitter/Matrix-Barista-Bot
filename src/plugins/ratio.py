import logging
import os
import random

from aiohttp import web

from plugins.base_plugin import BasePlugin

LOG = logging.getLogger(__name__)


class RatioPlugin(BasePlugin):
    def __init__(self):
        self.should_ratio = False

    def load(self, room, web_app, web_admin):
        web_admin.router.add_post("/plugins/ratio/trigger_next", self.trigger_next)

    def unload(self):
        pass

    async def periodic_task(self):
        pass

    async def message_listener(self, message):
        chance = os.getenv("RATIO_CHANCE")
        if chance is not None:
            try:
                chance = int(chance)
                ratio = None
                if self.should_ratio:
                    ratio = self.get_ratio()
                    self.should_ratio = False
                elif chance >= 1 and random.randint(1, 100) <= chance:
                    ratio = self.get_ratio()
                if ratio is not None:
                    await message.bridge.send_message(message.room_id, text=ratio)
            except TypeError:
                pass

    def get_commands(self):
        return {}

    def get_name(self):
        return "Ratio"

    def get_help(self):
        return "Randomly responds by ratioing the above message"

    async def trigger_next(self, request):
        self.should_ratio = True
        return web.Response(text='ok', content_type="text/html")

    def get_ratio(self):
        # Current data used for ratio generation
        prefix = ["L", "Ratio"]
        insult = ["You done messed up", "Reaction score", "Upset", "You moron",
                  "Percentile"]
        corporate = ["No synergy", "Touchbase", "HR'd",
                     "Get ping'd", "Overtime"]
        coding = ["Syntax error", "Semicolon'd", "Out of memory",
                  "Garbage collected", "/dev/null"]
        boardgame = ["Natural 1", "Checkmate", "Analysis paralysis",
                     "En passant", "Reverse card", "Trap card", "King me"]
        rent = ["Over priced", "Landlorded", "Renters agreement",
                "Rent to OWNed", "No water"]
        hacker = ["Social engineered", "Wacky digits", "Agent Surefire'd", "Literally in your system", "No anti-virus"]
        stock = ["Stonked", "Not financial advice", "Paper hands", "Bought the dip", "Went broke"]
        crypt = ["Gas priced", "Thanks for the NFT", "Pump and dump'd",
                 "Screenshotted", "Fungible", "Right clicked"]
        chef = ["Overcooked", "Toasted", "Burned", "Roasted", "Raw", "Unseasoned", "Eggless coffee"]
        elden = ["No Maidens", "Your sword has shoddy craftsmanship",
                 "Your treasure hoard is empty", "No vigor"]
        dino = ["Extinct", "Fossilized", "Stuck in tar"]
        cringe = ["Cringe", "Cope", "Ok boomer", "You are not just a clown you are the entire circus"]
        rude = ["Didn't ask", "Don't care", "Skill issue"]
        news = ["Fake news", "That's made up", "Old news bro", "So yesterday"]
        reddit = ["Reddit silver", "No upvotes", "Go tell Reddit", "Log off", "You're going in my cringe compilation"]
        pirate = ["Plundered", "Pillaged", "I found yer treasure",
                  "Davy Jones don't even want the likes of ye in his locker", "Shipwrecked", "No booty",
                  "All yer wenches be servicin' my crew"]
        caveman = ["Me have bigger cave", "Me not care", "Small meat stick", "Touch rock", "Never breed",
                   "You not only Ooga but entire Chakalaka"]
        french = ["You are english", "Mind your own business", "Boil your bottoms", "You're the son of a silly person",
                  "I blow my nose at you", "'So called'", "Your KNNH-Knights are silly",
                  "Block me before I taunt you a second time"]
        tf2 = ["Red spy in the base", "No medics", "Flag stolen", "I have more crates than you", "Not MANN enough"]
        fish = ["Not enough bait", "Weak hook", "I catch more fish than you"]
        windows = ["Windows user", "Incoming Windows update", "Bill-Gated", "Reinstall your OS"]
        question = ["Dignity?", "Self-esteem?", "Honor?", "self-respect?", "decency?", "restraint?", "reserve?",
                    "respectability?", "pride?", "modesty?", "manners?", "chastity?", "embarrassment?", "shame?",
                    "discretion?", "temperance?", "caution?", "consideration for one's own person?"]

        ratio_list = [insult, corporate, coding, boardgame, rent, hacker, stock,
                      crypt, chef, elden, dino, cringe, rude, news, reddit, pirate,
                      caveman, french, tf2, fish, windows, question]

        base = []
        data_set = random.choice(ratio_list)

        if len(data_set) >= 3:
            response0 = random.choice(prefix)
            base.append(response0)
            base.append(" + ")

            response1 = random.choice(data_set)
            base.append(response1)
            data_set.remove(response1)
            base.append(" + ")

            response2 = random.choice(data_set)
            base.append(response2)
            data_set.remove(response2)
            base.append(" + ")

            response3 = random.choice(data_set)
            base.append(response3)
            data_set.remove(response3)

            response = ""
            for phrase in base:
                response += "{}".format(phrase)

            return response
        return None
