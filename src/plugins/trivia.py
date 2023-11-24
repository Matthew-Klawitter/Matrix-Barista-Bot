import random
from nltk.metrics.distance import jaro_winkler_similarity

class TriviaPlugin:
    def get_commands(self):
        return {"trivia": self.trivia}

    def get_name(self):
        return "Trivia"

    def get_help(self):
        return "/trivia to start a game"

    def load(self, room, web_app, web_admin):
        self.games = {}
        self.current_games = {}
        with open("/res/trivia.txt") as f:
            new_game = None
            game_round = None
            for line in f.readlines():
                line = line.strip()
                if not new_game:
                    new_game = TriviaGame()
                    self.games[line] = new_game
                elif not game_round:
                    if line:
                        game_round = TriviaRound(line)
                    else:
                        new_game = None
                elif not line:
                    new_game.rounds.append(game_round)
                    game_round = None
                else:
                    game_round.answers.append(line.lower())

    async def message_listener(self, message):
        current_game = self.current_games.get(message.room_id, None)
        if not current_game:
            return
        if message.username not in current_game.scores:
            current_game.scores[message.username] = 0

        msg = message.message.lower()

        current_game.guesses += 1
        if "skip" in msg:
            current_game.skips += 1

        text = ""
        next_question = False
        if current_game.check_answer(msg):
            text = f"Correct! {message.username} got '{current_game.get_answer()}'\n"
            current_game.scores[message.username] += 1

            next_question = True
        elif current_game.guesses >= 10:
            text = f"No one got it right! The answer was {current_game.get_answer()}\n"
            next_question = True
        elif current_game.skips > 2:
            text = f"Skipping question! The answer was {current_game.get_answer()}\n"
            next_question = True

        if next_question:
            current_game.current_index += 1
            if current_game.current_index >= len(current_game.rounds):

                text += "Game over!\n"
                for user, score in sorted(
                        current_game.scores.items(), key=lambda item: item[1],
                        reverse=True):
                    text += f"{user}    {score}\n"
                current_game.current_index = 0
                current_game.scores = {}
                del self.current_games[message.room_id]
                await message.bridge.send_message(message.room_id, text=text)
            else:
                text += f"""Round {current_game.current_index + 1}

{current_game.current_question()}"""
                await message.bridge.send_message(message.room_id, text=text)

    async def trivia(self, message):
        current_game = self.current_games.get(message.room_id, None)
        if not current_game:
            title, game = random.choice(list(self.games.items()))
            self.current_games[message.room_id] = game
            text = f"""Welcome to trivia night!
{title} is the game.
Starting round 1.
{game.current_question()}
"""
            await message.bridge.send_message(message.room_id, text=text)
        else:
            await message.bridge.send_message(
                message.room_id, text="A game is already in progress!")


class TriviaRound():
    def __init__(self, question):
        self.question = question
        self.answers = []

    def check_answer(self, guess):
        guess = guess.lower().strip()
        for answer in self.answers:
            distance = jaro_winkler_similarity(guess, answer)
            if distance > 0.8:
                return True
        return False

    def get_answer(self):
        return " or ".join(self.answers)


class TriviaGame():
    def __init__(self):
        self.rounds = []
        self.scores = {}
        self.current_index = 0
        self.skips = 0
        self.guesses = 0

    def current_question(self):
        self.skips = 0
        self.guesses = 0
        return self.rounds[self.current_index].question

    def check_answer(self, guess):
        return self.rounds[self.current_index].check_answer(guess)

    def get_answer(self):
        return self.rounds[self.current_index].get_answer()
