import asyncio
import datetime
import json
import os
import socket
import sys
import getpass
from struct import pack, unpack
from time import sleep

from nio import AsyncClient, LoginResponse, MatrixRoom, RoomMessageText

from src.api.bridge import APIBridge
from src.api.data_objects import Command

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


async def message_callback(room: MatrixRoom, event: RoomMessageText) -> None:
    prefix = event.body.split(" ")[0]
    command = Command(prefix, room.user_name(event.sender), room.room_id, room.display_name, event.body)

async def connected_users(host="localhost", port=64738):
    """
        <host> [<port>]
        Ping the server and display results.
    """

    try:
        addrinfo = socket.getaddrinfo(host, port, 0, 0, socket.SOL_UDP)
    except socket.gaierror as e:
        print(e)
        return

    for (family, socktype, proto, canonname, sockaddr) in addrinfo:
        s = socket.socket(family, socktype, proto=proto)
        s.settimeout(2)

        buf = pack(">iQ", 0, datetime.datetime.now().microsecond)
        try:
            s.sendto(buf, sockaddr)
        except (socket.gaierror, socket.timeout) as e:
            continue

        try:
            data, addr = s.recvfrom(1024)
        except socket.timeout:
            continue

        r = unpack(">bbbbQiii", data)

        # version = r[1:4]
        # https://wiki.mumble.info/wiki/Protocol
        # r[0,1,2,3] = version
        # r[4] = ts (indent value)
        # r[5] = users
        # r[6] = max users
        # r[7] = bandwidth

        return r[5]

async def return_status(current_users, api, room):
    updated_users = await connected_users()
    new_current = current_users

    if updated_users != current_users:
        message = ""

        if current_users < updated_users:
            message = "A user has joined the mumble server. There are now " + str(
                updated_users) + " connected."
            new_current = updated_users
        elif current_users > updated_users:
            message = "A user has left the mumble server. There are now " + str(
                updated_users) + " connected."
            new_current = updated_users

        await api.send_message(room, message)
    sleep(1)
    return new_current

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

        current_users = await connected_users()

        while True:
            current_users = await return_status(current_users, bridge, room)

        # Run a one time sync to ignore old messages
        await client.sync(timeout=10000, full_state=True)
        client.add_event_callback(message_callback, RoomMessageText)
        await client.sync_forever(timeout=30000)

    # Either way we're logged in here, too
    await client.close()


asyncio.get_event_loop().run_until_complete(main())
