import asyncio
import getpass
import json
import os
import sys

from nio import AsyncClient, LoginResponse, RoomMessageText

from api.bridge import APIBridge
from plugins.plugin_manager import PluginManager
from services.mumble_alerts import MumbleAlerts

CONFIG_FILE = "credentials.json"


def write_details_to_disk(resp: LoginResponse, homeserver, defaultroom) -> None:
    """Writes the required login details to disk so we can log in later without
    using a password.

    Arguments:
        resp {LoginResponse} -- the successful client login response.
        homeserver -- URL of homeserver, e.g. "https://matrix.example.org"
    """
    # open the config file in write-mode
    with open(CONFIG_FILE, "w") as f:
        # write the login details to disk
        json.dump(
            {
                "homeserver": homeserver,  # e.g. "https://matrix.example.org"
                "user_id": resp.user_id,  # e.g. "@user:example.org"
                "device_id": resp.device_id,  # device ID, 10 uppercase letters
                "access_token": resp.access_token,  # cryptogr. access token
                "default_room": defaultroom
            },
            f
        )


async def periodic(services, timeout):
    while True:
        for s in services:
            await s.task()
        await asyncio.sleep(timeout)


async def main() -> None:
    # If there are no previously-saved credentials, we'll use the password
    if not os.path.exists(CONFIG_FILE):
        print("First time use. Did not find credential file. Asking for "
              "homeserver, user, and password to create credential file.")
        homeserver = "https://matrix.org"
        homeserver = input(f"Enter your homeserver URL: [{homeserver}] ")

        if not (homeserver.startswith("https://")
                or homeserver.startswith("http://")):
            homeserver = "https://" + homeserver

        user_id = "@user:example.org"
        user_id = input(f"Enter your full user ID: [{user_id}] ")

        default_room = "!roomid:example.org"
        default_room = input(f"Enter room id for test message: [{default_room}] ")

        device_name = "matrix-nio"
        device_name = input(f"Choose a name for this device: [{device_name}] ")

        client = AsyncClient(homeserver, user_id)
        pw = getpass.getpass()

        resp = await client.login(pw, device_name=device_name)

        # check that we logged in succesfully
        if (isinstance(resp, LoginResponse)):
            write_details_to_disk(resp, homeserver, default_room)
        else:
            print(f"homeserver = \"{homeserver}\"; user = \"{user_id}\"")
            print(f"Failed to log in: {resp}")
            sys.exit(1)

        print("Logged in using a password. Credentials were stored.")

    # Otherwise the config file exists, so we'll use the stored credentials
    else:
        # open the file in read-only mode
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            client = AsyncClient(config['homeserver'])

            client.access_token = config['access_token']
            client.user_id = config['user_id']
            client.device_id = config['device_id']

        room = config['default_room']
        bridge = APIBridge(client)

        print("Pre-initialization is complete!")

        '''
        Plugin Manager handles plugin initialization and mapping commands
        to their associated objects.
        '''
        plugin_manager = PluginManager(bridge)
        await plugin_manager.map_commands()

        '''
        The periodic loop handles services that should be run periodically.
        This would include such things as plugins that must be run once
        every second.
        '''
        services = [MumbleAlerts(bridge, room)]
        periodic_loop = asyncio.create_task(periodic(services, 1))
        print("Periodic service initialization is complete!")

        '''
        A set of callbacks intended to handle responding to user inputs.
        A plugin effectively registers a set of commands, and in these
        callbacks the bot will be looking for one of those sets to
        issue an appropriate response.
        '''
        print("Syncing messaging and callbacks with Matrix Synapse... Should be all set to pour!")
        await client.sync(timeout=0, full_state=True)  # Sync once to omit old messages
        print("Done with initial sync")
        client.add_event_callback(plugin_manager.message, RoomMessageText)
        await client.sync_forever(timeout=1000)

    # logout after finishing execution
    await client.close()

print("MatrixBaristaBot is brewing up...")
asyncio.get_event_loop().run_until_complete(main())
