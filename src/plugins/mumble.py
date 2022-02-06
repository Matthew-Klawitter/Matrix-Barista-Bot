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
                self.audio_file.write(soundchunk.pcm)
            except Exception as e:
                LOG.error(e)

        self.mumble = Mumble(server, nick, password=pwd)
        self.mumble.callbacks.set_callback(PCS, sound_received_handler)
        self.mumble.set_receive_sound(1)  # we want to receive sound
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
        clipped_name = self.audio_file.close()
        await message.bridge.send_audio(message.room_id, clipped_name)
        self.create_audio_file()


class AudioFile():
    BITRATE = 48000
    SECONDS = 60

    def __init__(self, name):
        DEBUG_ENCODER = True

        self.base_name = name
        self.name = name
        self.name += ".wav"

        self.file_obj = wave.open(self.name, "wb")
        self.file_obj.setparams((1, 2, AudioFile.BITRATE, 0, 'NONE', 'not compressed'))
        self.type = "wav"

    def write(self, data):
        self.file_obj.writeframes(data)

    def close(self):
        self.file_obj.close()

        start_frame = max(0, self.file_obj.getnframes() - AudioFile.SECONDS*AudioFile.BITRATE)

        read_obj = wave.open(self.name, "rb")
        read_obj.setpos(start_frame)
        audio_bytes = read_obj.readframes(self.file_obj.getnframes() - start_frame)
        read_obj.close()

        clipped_name = f"{self.base_name}-clip.wav"
        clipped_obj = wave.open(clipped_name, "wb")
        clipped_obj.setparams((1, 2, AudioFile.BITRATE, 0, 'NONE', 'not compressed'))
        clipped_obj.writeframes(audio_bytes)
        clipped_obj.close()

        return clipped_name
