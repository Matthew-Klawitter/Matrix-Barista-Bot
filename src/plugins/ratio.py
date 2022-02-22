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
        regular_ratio = ["L", "Ratio", "I'm a Chad", "You fell off",
            "You done messed up", "Reaction score", "Upset", "Not a bot",
            "You moron", "Dumber than a bot", "Percentile"]
        corporate_ratio = ["No synergy", "Touchbase", "HR'd",
            "Get ping'd", "Overtime"]
        coding_ratio = ["Syntax error", "Semicolon'd", "Out of memory",
            "Garbage collected", "/dev/null"]
        boardgame_ratio = ["Natural 1", "Checkmate", "Analysis paralysis",
            "En passant", "Reverse card", "Trap card", "King me"]
        rent_ratio = ["Over priced", "Landlorded", "Renters agreement", 
            "Rent to OWNed", "No water"]
        hacker_ratio = ["Social engineered", "Wacky digits", "Agent Surefire'd"]
        stock_ratio = ["Stonked", "Not financial advice", "Paper hands", "Bought the dip"]
        crypt_ratio = ["Gas priced", "Thanks for the NFT", "Pump and dump'd",
            "Screenshotted", "Fungible", "Right clicked"]
        chef_ratio = ["Overcooked", "Toasted", "Burned", "Roasted"]
        
        ratio_list = [regular_ratio, corporate_ratio, coding_ratio,
            boardgame_ratio, rent_ratio, hacker_ratio, stock_ratio, crypt_ratio, chef_ratio]

        data_set = random.choice(ratio_list)

        if (len(data_set) >= 3):
            response1 = random.choice(data_set)
            data_set.remove(response1)
            response2 = random.choice(data_set)
            data_set.remove(response2)
            response3 = random.choice(data_set)
            return "{} + {} + {}".format(response1, response2, response3)
        return None