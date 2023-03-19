import difflib
import json
import logging
import time
import os
import wave
import subprocess

from aiohttp import web
from pymumble_py3 import Mumble
from pymumble_py3.callbacks import PYMUMBLE_CLBK_SOUNDRECEIVED as PCS

from plugins.base_plugin import BasePlugin

LOG = logging.getLogger(__name__)


class MumblePlugin(BasePlugin):

    def load(self, room, web_app, web_admin):
        pwd = os.getenv("MUMBLE_PASS")
        server = os.getenv("MUMBLE_SERVER")
        nick = "ClipBot"

        def sound_received_handler(user, soundchunk):
            try:
                self.audio_file.write(user["name"], soundchunk.pcm)
            except Exception as e:
                LOG.error(e)

        self.mumble = Mumble(server, nick, password=pwd)

        self.mumble.callbacks.set_callback(PCS, sound_received_handler)
        self.mumble.set_receive_sound(1)

        self.mumble.start()
        self.create_audio_file()

        # Serve useful data our mumble client gathers
        self.setup_routes(web_admin)
        web_app.router.add_get("/plugins/mumble/clip", self.clip_route)
        web_app.router.add_get("/plugins/mumble/file", self.file_route)
        web_app.router.add_get("/plugins/mumble/submit", self.submit_clip_route)

    def unload(self):
        pass

    def periodic_task(self):
        pass

    async def message_listener(self, message):
        pass

    def setup_routes(self, web_admin):
        web_admin.router.add_get("/plugins/mumble/connected", self.connected_users)
        web_admin.router.add_get("/plugins/mumble/users", self.get_users)

    def clip_route(self, request):
        return web.FileResponse("/res/clip.html")

    def file_route(self, request):
        return web.FileResponse(f'/tmp/{request.query["path"]}')

    def submit_clip_route(self, request):
        mn = float(request.query["min"])
        mx = float(request.query["max"])
        file = f'/tmp/{request.query["path"]}'
        name = request.query["name"]
        duration = mx - mn
        subprocess.run(
            ["ffmpeg", "-i", file, "-ss", str(mn), "-t", str(duration), "-acodec", "copy", f"/out/{name}.wav"])
        return web.json_response({})

    def create_audio_file(self):
        audio_file_name = os.path.join("/tmp/", "mumble-%s" % time.strftime("%Y%m%d-%H%M%S"))
        self.audio_file = AudioFile(audio_file_name)

    def get_commands(self):
        return {"clip": self.clip}

    def get_name(self):
        return "Clippy"

    def get_help(self):
        return "!clip to save a mumble clip"

    async def clip(self, message):
        clipped_names = self.audio_file.close(message.args)
        for clipped_name in clipped_names:
            if "WEB_URL" in os.environ:
                url = f'{os.environ.get("WEB_URL")}/plugins/mumble/clip?file={os.path.basename(clipped_name)}'
                await message.bridge.send_message(message.room_id, url)
            await message.bridge.send_audio(message.room_id, clipped_name)
        self.create_audio_file()

    async def connected_users(self, request):
        connected = self.mumble.users.count()
        res = {"amount": connected}
        return web.json_response(res)

    async def get_users(self, request):
        users = self.mumble.users
        res = json.dumps(users)
        return web.json_response(res)


class AudioFile():
    BITRATE = 48000
    SECONDS = int(os.getenv("MUMBLE_CLIP_LENGTH"))

    def __init__(self, name):
        DEBUG_ENCODER = True

        self.base_name = name
        self.files = {}
        self.type = "wav"

    def get_name(self, username):
        return f"{self.base_name}-{username}.wav"

    def write(self, username, data):
        if username not in self.files:
            file_obj = wave.open(self.get_name(username), "wb")
            file_obj.setparams((1, 2, AudioFile.BITRATE, 0, 'NONE', 'not compressed'))
            self.files[username] = file_obj
        self.files[username].writeframes(data)

    def close(self, username):
        clipped_names = []

        ratio = float(os.environ.get("MUMBLE_CLIP_RATIO", 0.7))

        for name, file_obj in self.files.items():
            if username and not self.is_similar(username, name, ratio):
                continue
            file_obj.close()

            start_frame = max(0, file_obj.getnframes() - AudioFile.SECONDS * AudioFile.BITRATE)

            read_obj = wave.open(self.get_name(name), "rb")
            read_obj.setpos(start_frame)
            audio_bytes = read_obj.readframes(file_obj.getnframes() - start_frame)
            read_obj.close()

            clipped_name = f"{self.base_name}-{name}-clip.wav"
            clipped_obj = wave.open(clipped_name, "wb")
            clipped_obj.setparams((1, 2, AudioFile.BITRATE, 0, 'NONE', 'not compressed'))
            clipped_obj.writeframes(audio_bytes)
            clipped_obj.close()
            clipped_names.append(clipped_name)

        return clipped_names

    def is_similar(self, username, mumble_name, ratio):
        return difflib.SequenceMatcher(None, username, mumble_name).ratio() > ratio
