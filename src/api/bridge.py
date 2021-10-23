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

    async def send_message(self, room_id, message):
        try:
            limit = 1000000
            if len(message) > limit:
                message = f"{message[:limit]} [truncated]"
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message
                }
            )

        except Exception:
            LOG.error("Failed to send message.")

    async def send_html(self, room_id, message):
        try:
            limit = 1000000

            soup = bs.BeautifulSoup(message, "html.parser")
            for data in soup(['style', 'script']):
                data.decompose()
            clean_message = ' '.join(soup.stripped_strings)

            if len(message) > limit:
                message = f"{message[:limit]} [truncated]"
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": clean_message,
                    "format": "org.matrix.custom.html",
                    "formatted_body": message
                }
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
