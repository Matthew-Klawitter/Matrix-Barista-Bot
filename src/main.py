import asyncio
import os
import sys
import json
import getpass
import logging
import requests

from typing import Optional, Any, Coroutine, Callable, Tuple

from aiohttp import web
from aiohttp import web
from nio import (AsyncClient, ClientConfig, DevicesError, Event, InviteEvent, LoginResponse,
                 LocalProtocolError, MatrixRoom, MatrixUser, RoomMessageText,
                 crypto, exceptions, RoomSendResponse)

from tortoise import Tortoise, run_async

from api.bridge import APIBridge
from plugin_manager import PluginManager
from services.mumble_log import MumbleAlerts

LOG = logging.getLogger(__name__)

STORE_FOLDER = "nio_store/"


async def load_credentials(client=None):
    credentials = {
        "homeserver": os.getenv("MATRIX_HOMESERVER"),
        "user_id": os.getenv("MATRIX_USER"),
        "password": os.getenv("MATRIX_PASS"),
        "default_room": os.getenv("MATRIX_ROOM"),
    }
    if client is None:
        config = ClientConfig(store_sync_tokens=True)
        client = CustomEncryptedClient(
            credentials["homeserver"],
            credentials["user_id"],
            store_path=STORE_FOLDER,
            config=config,
            default_room=credentials["default_room"]
        )
    LOG.info("Logging in")
    resp = await client.login(credentials["password"])
    if (isinstance(resp, LoginResponse)):
        LOG.info("Log in sucessful")
        return client
    else:
        LOG.error("Log in failed with password")
        raise Exception(f"Failed to log in: {resp}")


async def get_client():
    client = await load_credentials()
    client.load_store()
    return client


async def init_database():
    username = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")
    connection_string = "postgres://{username}:{password}@postgres:5432/{database}".format(username=username,
                                                                                           password=password,
                                                                                           database=database)

    await Tortoise.init(
        db_url=connection_string,
        modules={'models': ['models.models']}
    )
    await Tortoise.generate_schemas()


class CustomEncryptedClient(AsyncClient):
    def __init__(self, homeserver, user='', device_id='', store_path='', config=None, ssl=None, proxy=None,
                 default_room=None):
        super().__init__(homeserver, user=user, device_id=device_id, store_path=store_path, config=config, ssl=ssl,
                         proxy=proxy)

        if store_path and not os.path.isdir(store_path):
            os.mkdir(store_path)
        self.default_room = default_room
        self.user = user

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


def token_auth_middleware(auth_scheme: str = 'Token', exclude_routes: Tuple = tuple(),
                          exclude_methods: Tuple = tuple()) -> Coroutine:
    """
    Checks an auth token and adds a user from user_loader in request
    """
    @web.middleware
    async def auth_handler(request, handler):
        try:
            scheme, token = request.headers["Authorization"].strip().split(' ')
        except KeyError:
            raise web.HTTPUnauthorized(reason="Missing authorization header")
        except ValueError:
            raise web.HTTPForbidden(reason="Invalid authorization header")

        if auth_scheme.lower() != scheme.lower():
            raise web.HTTPForbidden(reason="Invalid token scheme")

        if await check_token(token):
            return await handler(request)
        else:
            raise web.HTTPForbidden(reason="Token does not exist")
    return auth_handler


async def check_token(token: str):
    return token == os.getenv("WEB_AUTH_TOKEN")


async def main():
    try:
        #LOG.info("Attempting to connect to database...")
        #await init_database()
        web_app = web.Application(client_max_size=int(os.getenv("WEB_CLIENT_MAX_SIZE")))
        web_admin = web.Application(client_max_size=int(os.getenv("WEB_CLIENT_MAX_SIZE")),
                                    middlewares=[token_auth_middleware()])
        LOG.info("Created web app")
        #LOG.info("Connected to database.")
        client = await(get_client())
        LOG.info("Got client")
        bridge = APIBridge(client)
        LOG.info("Created Bridge")
        plugin_manager = PluginManager(bridge, client.default_room, client.user, web_app, web_admin)
        LOG.info("Created PluginManager")
        client.add_event_callback(plugin_manager.message_callback, RoomMessageText)
        LOG.info("Starting services...")
        services = [MumbleAlerts(bridge, client.default_room)]
        periodic_loop = asyncio.create_task(periodic(services, 1))
        LOG.info("Finished created services.")

        LOG.info("Attempting to start rest services services...")
        web_app.add_subapp('/admin/', web_admin)
        runner = web.AppRunner(web_app)
        await runner.setup()
        site = web.TCPSite(runner, 'matrix-bot', int(os.getenv("WEB_PORT")))
        await site.start()
        LOG.info("Rest services running ")

        await run_client(client)
    except (asyncio.CancelledError, KeyboardInterrupt):
        await client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        LOG.info("Doing more things")
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        pass
