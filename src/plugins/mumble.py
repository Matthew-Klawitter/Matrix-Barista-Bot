import logging
import time
import os
import wave

from pymumble_py3 import Mumble
from pymumble_py3.callbacks import PYMUMBLE_CLBK_SOUNDRECEIVED as PCS

LOG = logging.getLogger(__name__)

class MumblePlugin:

    def load(self, room):
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
            await message.bridge.send_audio(message.room_id, clipped_name)
        self.create_audio_file()


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
        for name, file_obj in self.files.items():
            if username and name != username:
                continue
            file_obj.close()

            start_frame = max(0, file_obj.getnframes() - AudioFile.SECONDS*AudioFile.BITRATE)

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
