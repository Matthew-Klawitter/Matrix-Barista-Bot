import asyncio
import datetime
import socket
from struct import pack, unpack
from time import sleep


class MumbleAlerts:
    def __init__(self, bridge, room):
        self.bridge = bridge
        self.room = room
        self.current_users = None

    async def task(self):
        if self.current_users is None:
            self.current_users = await self.connected_users()
        self.current_users = await self.return_status(self.current_users, self.bridge, self.room)

    async def connected_users(self, host="localhost", port=64738):
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

    async def return_status(self, current_users, bridge, room):
        updated_users = await self.connected_users()
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

            await bridge.send_message(room, message)
        return new_current
