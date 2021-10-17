import getpass

from api.bridge import APIBridge, CustomClient
from plugin_manager import PluginManager
# from services.mumble_alerts import MumbleAlerts
from services.mumble_log import MumbleAlerts
# from services.mc_alerts import MCAlerts

CONFIG_FILE = "credentials.json"
LOG = logging.getLogger(__name__)

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
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    # If there are no previously-saved credentials, we'll use the password
    if not os.path.exists(CONFIG_FILE):
        client = CustomClient(homeserver, user_id, home_room=room, config=ClientConfig())
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
            room = config['default_room']
            client = CustomClient(config['homeserver'], home_room=room, config=ClientConfig())

            client.access_token = config['access_token']
            client.user_id = config['user_id']
            client.device_id = config['device_id']

        bridge = APIBridge(client)

        LOG.info(f"Loaded config {CONFIG_FILE}")

        '''
        Plugin Manager handles plugin initialization and mapping commands
        to their associated objects.
        '''
        plugin_manager = PluginManager(bridge)

        '''
        The periodic loop handles services that should be run periodically.
        This would include such things as plugins that must be run once
        every second.
        '''
        services = [MumbleAlerts(bridge, room)] #, MCAlerts(bridge, room)]
        periodic_loop = asyncio.create_task(periodic(services, 1))

        '''
        A set of callbacks intended to handle responding to user inputs.
        A plugin effectively registers a set of commands, and in these
        callbacks the bot will be looking for one of those sets to
        issue an appropriate response.
        '''
        LOG.info(f"Syncing")
        after_first_sync_task = asyncio.ensure_future(client.after_first_sync())
        await client.sync(timeout=0, full_state=True)  # Sync once to omit old messages
        client.add_event_callback(plugin_manager.message_callback, RoomMessageText)
        LOG.info(f"Syncing forever")
        sync_forever_task = asyncio.ensure_future(client.sync_forever(timeout=1000))
        await asyncio.gather(
            after_first_sync_task,
            sync_forever_task
        )

    # logout after finishing execution
    await client.close()

asyncio.get_event_loop().run_until_complete(main())