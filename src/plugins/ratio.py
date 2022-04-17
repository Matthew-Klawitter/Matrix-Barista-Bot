import logging
import os
import random

LOG = logging.getLogger(__name__)

class RatioPlugin:
    def load(self, room):
        pass

    def get_commands(self):
        return {}

    def get_name(self):
        return "Ratio"

    def get_help(self):
        return "Randomly responds by ratioing the above message"

    async def message_listener(self, message):
        chance = os.getenv("RATIO_CHANCE")
        if (chance is not None):
            try:
                chance = int(chance)
                if (chance >= 1 and random.randint(1, 100) <= chance):
                    ratio = self.get_ratio()

                    if (ratio is not None):
                        await message.bridge.send_message(message.room_id, text=ratio)
            except TypeError:
                pass           

    def get_ratio(self):
        # Current data used for ratio generation
        general = ["L", "Ratio", "You fell off"]
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
        hacker = ["Social engineered", "Wacky digits", "Agent Surefire'd"]
        stock = ["Stonked", "Not financial advice", "Paper hands", "Bought the dip"]
        crypt = ["Gas priced", "Thanks for the NFT", "Pump and dump'd",
            "Screenshotted", "Fungible", "Right clicked"]
        chef = ["Overcooked", "Toasted", "Burned", "Roasted"]
        elden = ["No Maidens", "Your sword has shoddy craftsmanship",
            "Your treasure hoard is empty", "No vigor"]
        
        ratio_list = [insult, corporate, coding, boardgame, rent, hacker, stock,
            crypt, chef, elden]

        data_set = random.choice(ratio_list)

        if (len(data_set) >= 3):
            response0 = random.choice(general)
            response1 = random.choice(data_set)
            data_set.remove(response1)
            response2 = random.choice(data_set)
            data_set.remove(response2)
            response3 = random.choice(data_set)
            return "{} + {} + {} + {}".format(response0, response1, response2, response3)
        return None