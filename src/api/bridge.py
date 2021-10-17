import os
from PIL import Image
import aiofiles.os
import magic

from nio import AsyncClient, UploadResponse, MatrixRoom, InviteEvent

STORE_FOLDER = "nio_store/"

class CustomClient(AsyncClient):
    def __init__(self, *args, home_room=None, **kwargs):
        kwargs["store_path"] = STORE_FOLDER
        super().__init__(*args, **kwargs)
        store_path = kwargs["store_path"]
        if store_path and not os.path.isdir(store_path):
            os.mkdir(store_path)
        self.add_event_callback(self.cb_autojoin_room, InviteEvent)
        self.home_room = home_room

    def cb_autojoin_room(self, room: MatrixRoom, event: InviteEvent):
        self.join(room.room_id)
        room = self.rooms[ROOM_ID]
        print(f"Room {room.name} is encrypted: {room.encrypted}" )

    async def after_first_sync(self):
        await self.synced.wait()
        self.trust_devices()

    def trust_devices(self) -> None:
        print(self.home_room)
        for device_id, olm_device in self.device_store[user_id].items():
            if user_id == self.user_id and device_id == self.device_id:
                continue
            self.verify_device(olm_device)
            print(f"Trusting {device_id} from user {user_id}")

class APIBridge:
    def __init__(self, client):
        self.client = client

    async def send_message(self, room_id, message):
        try:
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message
                }
            )

        except Exception:
            print("Failed to send message.")

    async def send_image(self, room_id, image):
        mime_type = magic.from_file(image, mime=True)  # e.g. "image/jpeg"
        if not mime_type.startswith("image/"):
            print("Drop message because file does not have an image mime type.")
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
            print("Image was uploaded successfully to server. ")
        else:
            print(f"Failed to upload image. Failure response: {resp}")

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
            print("Image was sent successfully")
        except Exception:
            print(f"Image send of file {image} failed.")
