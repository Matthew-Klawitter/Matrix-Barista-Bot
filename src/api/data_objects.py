class Command:
    def __init__(self, prefix, username, chatroom_id, chatroom, msg):
        self.prefix = prefix
        self.username = username
        self.chatroom_id = chatroom_id
        self.chatroom = chatroom
        self.args = msg
