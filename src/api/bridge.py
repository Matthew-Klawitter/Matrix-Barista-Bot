import bs4 as bs
import os
from PIL import Image
import aiofiles.os
import magic

from nio import UploadResponse

import logging

LOG = logging.getLogger(__name__)

class APIBridge:
    def __init__(self, client):
        self.client = client

    def limit_message(self, message):
        limit = 1000000
        if len(message) > limit:
            return f"{message[:limit]} [truncated]"
        return message

    def html_to_text(self, message):
        soup = bs.BeautifulSoup(message, "html.parser")
        for data in soup(['style', 'script']):
            data.decompose()
        return ' '.join(soup.stripped_strings)

    async def send_message(self, room_id, text=None, html=None, msg_type="m.text", reply_to=None):
        content = {}
        if html:
            html = self.limit_message(html)
            text = self.html_to_text(html)
            content["format"] = "org.matrix.custom.html"
            content["formatted_body"] = html
        if text:
            text = self.limit_message(text)
        content["msgtype"] = msg_type
        content["body"] = text
        if reply_to:
            content["m.relates_to"] = {
                "rel_type": "m.thread",
                "event_id": reply_to,
                "is_falling_back": False, # don't show to user outside of thread
            }
        try:
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content=content
            )
        except Exception:
            LOG.error("Failed to send message.")

    async def send_image(self, room_id, image):
        mime_type = magic.from_file(image, mime=True)  # e.g. "image/jpeg"
        if not mime_type.startswith("image/"):
            LOG.error("Drop message because file does not have an image mime type.")
            return

        im = Image.open(image)
        (width, height) = im.size  # im.size returns (width,height) tuple

        # first do an upload of image, then send URI of upload to room
        file_stat = await aiofiles.os.stat(image)
        async with aiofiles.open(image, "r+b") as f:
            resp, maybe_keys = await self.client.upload(
                f,
                content_type=mime_type,  # image/jpeg
                filename=os.path.basename(image),
                filesize=file_stat.st_size)
        if isinstance(resp, UploadResponse):
            LOG.error("Image was uploaded successfully to server. ")
        else:
            LOG.error(f"Failed to upload image. Failure response: {resp}")

        content = {
            "body": os.path.basename(image),  # descriptive title
            "info": {
                "size": file_stat.st_size,
                "mimetype": mime_type,
                "thumbnail_info": None,  # TODO
                "w": width,  # width in pixel
                "h": height,  # height in pixel
                "thumbnail_url": None,  # TODO
            },
            "msgtype": "m.image",
            "url": resp.content_uri,
        }

        try:
            await self.client.room_send(
                room_id,
                message_type="m.room.message",
                content=content
            )
            LOG.info("Image was sent successfully")
        except Exception:
            LOG.error(f"Image send of file {image} failed.")

    async def send_audio(self, room_id, filepath):
        mime_type = "audio/wav"

        file_stat = await aiofiles.os.stat(filepath)
        async with aiofiles.open(filepath, "r+b") as f:
            resp, maybe_keys = await self.client.upload(
                f,
                content_type=mime_type,
                filename=os.path.basename(filepath),
                filesize=file_stat.st_size)
        if isinstance(resp, UploadResponse):
            LOG.error("File was uploaded successfully to server. ")
        else:
            LOG.error(f"Failed to upload file. Failure response: {resp}")

        content = {
            "body": os.path.basename(filepath),  # descriptive title
            "info": {
                "size": file_stat.st_size,
                "mimetype": mime_type,
            },
            "msgtype": "m.audio",
            "url": resp.content_uri,
        }

        try:
            await self.client.room_send(
                room_id,
                message_type="m.room.message",
                content=content
            )
            LOG.info("File was sent successfully")
        except Exception:
            LOG.error(f"File send of file {filepath} failed.")
