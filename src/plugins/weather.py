import requests
import en_core_web_sm
import logging

from plugins.base_plugin import BasePlugin

LOG = logging.getLogger(__name__)


class WeatherPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.api_key = None
        self.nlp = None

    def load(self, room, web_app, web_admin):
        self.nlp = en_core_web_sm.load()
        self.api_key = ""

    def unload(self):
        pass

    async def periodic_task(self):
        pass

    async def message_listener(self, message):
        LOG.info(message.message)

        weather = self.nlp("What's the weather in a city?")
        statement = self.nlp(message.message)
        min_similarity = 0.70
        city = ""
        similarity = weather.similarity(statement)
        LOG.info(similarity)

        if similarity >= min_similarity:
            for ent in statement.ents:
                if ent.label_ == "GPE":
                    city = ent.text
                    break
                else:
                    txt = "You need to also tell me what city to check the weather for."
                    await message.bridge.send_message(message.room_id, text=txt)
                    return

            city_weather = self.get_weather(city)
            if city_weather is not None:
                txt = "In " + city + ", the current weather is: " + city_weather
                await message.bridge.send_message(message.room_id, text=txt)
                return
            else:
                txt = "Something went wrong."
                await message.bridge.send_message(message.room_id, text=txt)
                return

    def get_commands(self):
        return {}

    def get_name(self):
        return "Weather"

    def get_help(self):
        return "Inquire in chat the weather in a city."

    def get_weather(self, city_name):
        api_url = "http://api.openweathermap.org/data/2.5/weather?q={}&appid={}".format(city_name, self.api_key)

        response = requests.get(api_url)
        response_dict = response.json()

        weather = response_dict["weather"][0]["description"]

        if response.status_code == 200:
            return weather
        else:
            print('[!] HTTP {0} calling [{1}]'.format(response.status_code, api_url))
            return None
