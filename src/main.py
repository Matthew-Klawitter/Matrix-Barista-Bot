import asyncio
import os
import sys
import json
import getpass
import logging

from typing import Optional

from nio import (AsyncClient, ClientConfig, DevicesError, Event,InviteEvent, LoginResponse,
                 LocalProtocolError, MatrixRoom, MatrixUser, RoomMessageText,
                 crypto, exceptions, RoomSendResponse)

from api.bridge import APIBridge
from plugin_manager import PluginManager
from services.mumble_log import MumbleAlerts

LOG = logging.getLogger(__name__)

STORE_FOLDER = "nio_store/"
CONFIG_FILE = "credentials.json"

async def load_credentials(client=None):
    LOG.info("Loading credentials")
    with open(CONFIG_FILE, "r") as f:
        LOG.info("Opened credentials file")
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
        LOG.info("Created client from existing credentials")
        client.user_id = credentials['user_id']
        client.access_token = credentials.get('access_token', '')
        client.device_id = credentials.get('device_id', '')
        LOG.info("Logging in")
        resp = await client.login(client.access_token, client.user_id, client.device_id)
        if (isinstance(resp, LoginResponse)):
            LOG.info("Log in sucessful")
            return client
        else:
            LOG.info("Log in with token failed, using password")
            resp = await client.login(credentials["password"])
            if (isinstance(resp, LoginResponse)):
                LOG.info("Log in sucessful")
                dump(
                    credentials["homeserver"],
                    resp.user_id,
                    resp.device_id,
                    resp.access_token,
                    credentials["default_room"],
                    credentials["password"]
                )
                return client
            else:
                LOG.error("Log in failed with password")
                raise Exception(f"Failed to log in: {resp}")

def dump(homeserver, user_id, device_id, access_token, default_room, password):
    with open(CONFIG_FILE, "w") as f:
        json.dump(
            {
                "homeserver": homeserver,  # e.g. "https://matrix.example.org"
                "user_id": user_id,  # e.g. "@user:example.org"
                "device_id": device_id,  # device ID, 10 uppercase letters
                "access_token": access_token,  # cryptogr. access token
                "default_room": default_room,
                "password": password,
            },
            f
        )

async def get_client():
    if os.path.isfile(CONFIG_FILE):
        LOG.info("Loading credentials from file")
        client = await load_credentials()
    else:
        LOG.error("No credential file found")
        raise Exception("No credential file found")
    client.load_store()
    return client


class CustomEncryptedClient(AsyncClient):
    def __init__(self, homeserver, user='', device_id='', store_path='', config=None, ssl=None, proxy=None, default_room=None):
        super().__init__(homeserver, user=user, device_id=device_id, store_path=store_path, config=config, ssl=ssl, proxy=proxy)

        if store_path and not os.path.isdir(store_path):
            os.mkdir(store_path)
        self.default_room = default_room

    def trust_devices(self) -> None:
        room_devices = self.room_devices(self.default_room)
        LOG.info(f"Checking for missing sessions")
        for user, devices in self.get_missing_sessions(self.default_room).items():
            for device in devices:
                self.verify_device(room_devices[user][device])
                LOG.info(f"Verifying device {device} for {user}")


async def run_client(client: CustomEncryptedClient) -> None:
    async def after_first_sync():
        await client.synced.wait()
        client.trust_devices()
        LOG.info(f"Finished first sync")
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
        LOG.info("Got client")
        bridge = APIBridge(client)
        LOG.info("Created Bridge")
        plugin_manager = PluginManager(bridge)
        LOG.info("Created PluginManager")
        client.add_event_callback(plugin_manager.message_callback, RoomMessageText)

        services = [MumbleAlerts(bridge, client.default_room)]
        periodic_loop = asyncio.create_task(periodic(services, 1))

        await run_client(client)
    except (asyncio.CancelledError, KeyboardInterrupt):
        await client.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        pass
