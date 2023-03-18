import os
import openai

class GPTPlugin:
    def load(self, room, web_app, web_admin):
        self.model = "gpt-3.5-turbo"
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        pass

    def get_commands(self):
        return {"gpt": self.chat_completion}

    def get_name(self):
        return "GPT"

    def get_help(self):
        return "!gpt as a reply or message"

    async def chat_completion(self, message):
        if message.is_reply:
            # Remove the username from the message
            content = message.replied_message.split(' ', 1)[1]
        else:
            content = message.args

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": content},
                ],
                max_tokens=100,
            )
            for choice in response["choices"]:
                res_text = choice["message"]["content"].strip()
                await message.bridge.send_message(
                    message.room_id, text=res_text)
        except Exception:
            await message.bridge.send_message(
                message.room_id, text="Sorry, API error")
