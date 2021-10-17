class Message:
    def __init__(self, bridge, room, event):
        self.username = room.user_name(event.sender)
        self.room_id = room.room_id
        self.room_name = room.display_name
        self.bridge = bridge
        self.message = event.body
        self.is_command = event.body.startswith("!")
        # Parsed message for correct command handling
        if self.is_command:
            parts = event.body[1:].split(" ", 1)
            self.command = parts[0]
            if len(parts) > 1:
                self.args = parts[1]
            else:
                self.args = ""
