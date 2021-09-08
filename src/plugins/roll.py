import random
import re


"""
Main Plugin class that manages command usage
"""


class DicePlugin:
    async def task(self, command):
        if command.prefix == "!r" or command.prefix == "!roll":
            await command.bridge.send_message(command.chatroom_id, await self.roll_dice(command))

    async def get_commands(self):
        return {"!r", "!roll"}

    async def get_name(self):
        return "Roll"

    async def get_help(self):
        return "/roll <dice_expression>\n"

    async def roll_dice(self, command):
        rolls = []
        constant = []
        parts = command.args.split("+")
        for part in parts:
            if "-" in part:
                try:
                    index = part.index("-", 1)
                    new_part = part[index:]
                    part = part[:index]
                    parts.append(new_part)
                except:
                    pass  # part is just a plain negative number
            part = part.strip()
            if re.search("\d+[dD]\d+", part):
                rolls.append(Roll(part))
            elif part.replace("-", "", 1).isdigit():
                constant.append(int(part))
        result = "Rolled:"
        total = 0
        for roll in rolls:
            total += roll.sum()
            result += "\n(" + ", ".join(str(s) for s in roll.rolls) + ") = " + str(roll.sum())
        for c in constant:
            total += c
            result += "\n + " + str(c)
        result += "\n = " + str(total)
        return result

"""
Class for handling dice rolls
"""


class Roll():
    def __init__(self, init_string):
        init_string = init_string.lower()
        parts = init_string.split("d")

        if parts[0]:
            self.num = max(int(parts[0]), 1)  # How many dice to roll
        else:
            self.num = 1

        if parts[1]:
            self.size = int(parts[1])  # The size of the dice (i.e. d20)

            if self.size < 1:
                self.size = 1  # The size of the dice must be greater than 1
        else:
            self.size = 1

        self.rolls = []  # A list containing all rolls made
        self.roll()  # Rolls self.num dice of dice size self.size and stores them in self.rolls

    def roll(self):
        if self.rolls:
            return self.rolls
        for i in range(self.num):
            self.rolls.append(random.randint(1, self.size))
        return self.rolls

    def sum(self):
        return sum(self.rolls)