import logging
import random
import shelve
import nltk
nltk.download('punkt')
nltk.download("stopwords")
nltk.download('averaged_perceptron_tagger')
nltk.download("vader_lexicon")
nltk.download('crubadan')
nltk.download('bcp47')
nltk.download('words')

from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import SyllableTokenizer

from aiohttp import web
from plugins.base_plugin import BasePlugin


LOG = logging.getLogger(__name__)


class SocialCreditPlugin(BasePlugin):
    def __init__(self):
        self.titles = None
        self.credit = None

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

    async def periodic_task(self, bridge):
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
        if "jerma" in msg:
            changes.append({
                "score": 10,
                "reason": random.choice([
                    "welcome to jerma craft",
                    "OH LOOK IT'S A SHPEE",
                    "AA EE OO! AudioJungle",
                    "I'm not tiny, I'm compact",
                ]),
            })

        base_score = 1

        try:
            if False and "http://" not in msg and "https://" not in msg:
                tokens = nltk.word_tokenize(msg)
                pos_tags = nltk.pos_tag(tokens)

                # Check for cheating by posting bad messages
                has_verb = any(t for t in pos_tags if t[1].startswith("VB"))
                has_noun = any(t for t in pos_tags if t[1].startswith("NN"))
                if not has_verb and not has_noun:
                    changes.append({
                        "score": -5,
                        "reason": "no noun nor verb",
                    })

                # Base score
                sia = SentimentIntensityAnalyzer()
                scores = sia.polarity_scores(msg)
                multi = (scores["neu"] + scores["pos"] - scores["neg"]*2)
                base_score = (len(tokens)/4) * multi
                if scores["neg"]*2 > scores["pos"]:
                    print("negative sentiment")
                    changes.append({
                        "score": base_score,
                        "reason": "message is bad for morale",
                    })

                SSP = SyllableTokenizer()
                longest = max(((s, len(SSP.tokenize(s))) for s in tokens), key=lambda x:x[1])
                if longest[1] > 4 and "http" not in longest[0]:
                    changes.append({
                        "score": longest[1],
                        "reason": f"good use of the word {longest[0]}",
                    })
        except:
            # No NLTK analysis
            LOG.error("Error with NLTK analysis, ignoring")
        with shelve.open("/data/credit", writeback=True) as data:
            self.credit = data["credit"]
            if changes:
                await message.bridge.send_message(message.room_id,
                    text="\n".join(
                        [f'{x["score"]:.2f}: {x["reason"]}' for x in changes]
                    ),
                    reply_to=message.event.event_id,
                )
                for change in changes:
                    self.credit[message.username]["score"] += change["score"]
            else:
                self.credit[message.username]["score"] += base_score
            data.sync()

    async def get_credit(self, message):
        for k, v in self.credit.items():
            txt = f"{v['title']} {k}, {v['score']}"
            await message.bridge.send_message(message.room_id, text=txt)
