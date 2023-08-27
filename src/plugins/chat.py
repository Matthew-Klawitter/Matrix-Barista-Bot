import re, os, random
import openai
import json
import urllib.request
import textwrap
from PIL import Image, ImageDraw, ImageFont

from asyncio import run

async def random_file(parent, message):
    files = os.listdir(parent)
    await message.bridge.send_image(message.room_id, parent + random.choice(files))

async def random_rip(message):
    await random_file("/res/rip/", message)

async def no(message):
    await message.bridge.send_image(message.room_id, "/res/no.jpeg")

async def send_ai_meme(message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": "Output JSON with a caption field and image field. The caption should be the text of a meme relating to workplace humor. The image field should be a description of this meme's image."
            },
        ],
        max_tokens=1000,
        temperature=0.8,
    )
    j = json.loads(response.choices[0]["message"]["content"])

    image = openai.Image.create(
      prompt=j["image"],
      n=2,
      size="512x512"
    )
    urllib.request.urlretrieve(image["data"][0]["url"], "/tmp/gpt_image.jpg")


    img = Image.open("/tmp/gpt_image.jpg")
    font = ImageFont.truetype("/res/COMIC.TTF", 48)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(textwrap.wrap(j["caption"], width=20)):
        draw.text((0, 50*i), line, fill='white', font=font, stroke_width=2, stroke_fill='black')

    img.save("/res/out.jpg")
    await message.bridge.send_image(message.room_id, "/res/out.jpg")

responses = (
    ( r"\brip\b", [random_rip] ),
    ( r"no\s\w+\?", [no] ),
    ( r"\bwork\b", [send_ai_meme] ),
    ( r"\bworking\b", [send_ai_meme] ),
)

class ChatPlugin:
    def load(self, room, web_app, web_admin):
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    def get_commands(self):
        return {}

    def get_name(self):
        return "General Chat"

    def get_help(self):
        return "Responds to messages\n"

    async def message_listener(self, message):
        if message.is_command:
            return

        msg = message.message.lower()
        for pattern, callbacks in responses:
            if re.search(pattern, msg, flags=re.IGNORECASE):
                try:
                    random_callback = random.choice(callbacks)
                    await random_callback(message)
                except Exception as e:
                    pass
