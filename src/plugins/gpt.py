import os
import openai
import logging

LOG = logging.getLogger(__name__)

class GPTPlugin:
    def load(self, room, web_app, web_admin):
        self.model = "gpt-3.5-turbo"
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        self.prompts = {}
        for filename in os.listdir("/res/gpt/"):
            with open("/res/gpt/"+filename) as f:
                self.prompts[filename] = f.read()

    def get_commands(self):
        return {
            "gpt": self.chat_completion,
            "prompt": self.use_prompt,
            "prompt_show": self.show_prompt,
            "prompt_list": self.list_prompts,
            "prompts": self.list_prompts,
            "prompt_save": self.save_prompt,
        }

    def get_name(self):
        return "GPT"

    def get_help(self):
        return "!gpt as a reply or message"

    async def list_prompts(self, message):
        if self.prompts:
            msg = "\n".join(list(self.prompts.keys()))
            await message.bridge.send_message(message.room_id, text=msg)
        else:
            await message.bridge.send_message(message.room_id, text="No prompts")

    async def save_prompt(self, message):
        name, prompt = message.args.split(" ", 1)
        with open("res/gpt/"+name, "w") as f:
            f.write(prompt)
        self.prompts[name] = prompt
        await message.bridge.send_message(
            message.room_id, text="Saved prompt " + name)

    async def use_prompt(self, message):
        name, prompt = message.args.split(" ", 1)
        if name in self.prompts:
            text = await self.get_completion(self.prompts[name] + prompt)
            await message.bridge.send_message(message.room_id, text=text, reply_to=message.event.event_id)
        else:
            await message.bridge.send_message(message.room_id, text=f"No such prompt '{name}'")

    async def show_prompt(self, message):
        name = message.args
        if name in self.prompts:
            text = self.prompts[name]
            await message.bridge.send_message(message.room_id, text=text, reply_to=message.event.event_id)
        else:
            await message.bridge.send_message(message.room_id, text=f"No such prompt '{name}'")

    async def get_completion(self, text):
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": text},
                ],
                max_tokens=1000,
            )
            res_text = " ".join([choice["message"]["content"].strip() for choice in response["choices"]])
            return res_text
        except Exception as e:
            return f"API issue {e}"

    def message_content(self, message):
        if message.is_reply:
            # Remove the username from the message
            return message.replied_message.split(' ', 1)[1]
        return message.args

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

