import asyncio
import os
import sys
import json
import getpass

from typing import Optional

from nio import (AsyncClient, ClientConfig, DevicesError, Event,InviteEvent, LoginResponse,
                 LocalProtocolError, MatrixRoom, MatrixUser, RoomMessageText,
                 crypto, exceptions, RoomSendResponse)

from api.bridge import APIBridge
from plugin_manager import PluginManager
from services.mumble_log import MumbleAlerts

STORE_FOLDER = "nio_store/"
CONFIG_FILE = "credentials.json"

async def load_credentials(client=None):
    with open(CONFIG_FILE, "r") as f:
        credentials = json.load(f)
        if client is None:
            config = ClientConfig(store_sync_tokens=True)
            client = CustomEncryptedClient(
                credentials["homeserver"],
                credentials["user_id"],
                store_path=STORE_FOLDER,
                config=config,
                default_room=credentials["default_room"],
            )
        client.user_id = credentials['user_id']
        client.access_token = credentials['access_token']
        client.device_id = credentials['device_id']
        await client.login(client.access_token, client.user_id, client.device_id)
        return client

async def create_credentials():
    print("Creating credentials")
    homeserver = input(f"Enter your homeserver URL: [https://matrix.org] ")
    if not (homeserver.startswith("https://")
            or homeserver.startswith("http://")):
        homeserver = "https://" + homeserver
    user_id = input(f"Enter your full user ID: [@user:example.org] ")
    default_room = input(f"Enter room id for test message: [!roomid:example.org] ")
    device_name = "matrix-nio"
    pw = getpass.getpass()

    config = ClientConfig(store_sync_tokens=True)
    client = CustomEncryptedClient(
        homeserver,
        user_id,
        store_path=STORE_FOLDER,
        config=config,
        default_room=default_room,
    )

    resp = await client.login(pw)
    with open(CONFIG_FILE, "w") as f:
        json.dump(
            {
                "homeserver": homeserver,  # e.g. "https://matrix.example.org"
                "user_id": resp.user_id,  # e.g. "@user:example.org"
                "device_id": resp.device_id,  # device ID, 10 uppercase letters
                "access_token": resp.access_token,  # cryptogr. access token
                "default_room": default_room
            },
            f
        )
    return client

async def get_client():
    if os.path.isfile(CONFIG_FILE):
        client = await load_credentials()
    else:
        client = await create_credentials()
    client.load_store()
    return client


class CustomEncryptedClient(AsyncClient):
    def __init__(self, homeserver, user='', device_id='', store_path='', config=None, ssl=None, proxy=None, default_room=None):
        super().__init__(homeserver, user=user, device_id=device_id, store_path=store_path, config=config, ssl=ssl, proxy=proxy)

        if store_path and not os.path.isdir(store_path):
            os.mkdir(store_path)
        self.default_room = default_room
        self.add_event_callback(self.cb_autojoin_room, InviteEvent)

    def trust_devices(self) -> None:
        room_devices = self.room_devices(self.default_room)
        for user, devices in self.get_missing_sessions(self.default_room).items():
            print(user)
            for device in devices:
                self.verify_device(room_devices[user][device])
                print(f"Verifying device {device} for {user}")

    def cb_autojoin_room(self, room: MatrixRoom, event: InviteEvent):
        self.join(room.room_id)
        room = self.rooms[ROOM_ID]
        print(f"Room {room.name} is encrypted: {room.encrypted}" )


async def run_client(client: CustomEncryptedClient) -> None:
    async def after_first_sync():
        await client.synced.wait()
        client.trust_devices()
    after_first_sync_task = asyncio.ensure_future(after_first_sync())
    sync_forever_task = asyncio.ensure_future(client.sync_forever(30000, full_state=True))
    await client.sync(timeout=0, full_state=True)
    await asyncio.gather(
        after_first_sync_task,
        sync_forever_task
    )

async def periodic(services, timeout):
    while True:
        for s in services:
            await s.task()
        await asyncio.sleep(timeout)

async def main():
    try:
        client = await(get_client())

        bridge = APIBridge(client)

        plugin_manager = PluginManager(bridge)
        client.add_event_callback(plugin_manager.message_callback, RoomMessageText)

        services = [MumbleAlerts(bridge, client.default_room)]
        periodic_loop = asyncio.create_task(periodic(services, 1))

        await run_client(client)



    except (asyncio.CancelledError, KeyboardInterrupt):
        await client.close()
if __name__ == "__main__":
    try:
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        pass
