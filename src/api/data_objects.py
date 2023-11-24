class Message:
    def __init__(self, bridge, room, event):
        self.username = room.user_name(event.sender)
        self.room_id = room.room_id
        self.room_name = room.display_name
        self.bridge = bridge
        self.message = event.body
        self.event = event

        try:
            # Check for reply
            event.source["content"]["m.relates_to"]["m.in_reply_to"]
            self.is_reply = True
            parts = event.body.splitlines()
            self.replied_message = parts[0]
            self.message = "\n".join(parts[2:])
        except Exception as e:
            self.is_reply = False
            pass

        # Parsed message for correct command handling
        self.is_command = self.message.startswith("!")
        if self.is_command:
            parts = self.message[1:].split(" ", 1)
            self.command = parts[0]
            if len(parts) > 1:
                self.args = parts[1]
            else:
                self.args = ""

