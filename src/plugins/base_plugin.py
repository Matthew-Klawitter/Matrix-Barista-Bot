from abc import ABC, abstractmethod

"""
Abstract class to be inherited by every plugin.

Plugins are automatically created and loaded when a class extending this ABC exists within
the plugin folder.
"""


class BasePlugin(ABC):

    @abstractmethod
    def load(self, room, web_app, web_admin):
        """
        Method called after a singleton instance of this object is created within the plugin_manager

        Parameters
        ----------
        room : str
            The main room the bot initial connects to.
        web_app : web.Application
            Public REST route for this plugin.
        web_admin : web.Application
            Secure REST route for this plugin.
        """
        pass

    @abstractmethod
    def unload(self):
        """
        Method called before removing instance of this plugin from the plugin manager.
        Allows for the plugin developer to gracefully stop operations on this plugin.
        """
        pass

    @abstractmethod
    async def periodic_task(self, bridge):
        """
        Method called periodically based on the applications global timeout.
        See also the main.py periodic method

        Parameters
        ----------
        bridge : ApiBridge
            Helper class to send responses back to the chatroom
        """
        pass

    @abstractmethod
    async def message_listener(self, message):
        """
        Called every time the bot reads a message in a chatroom.

        Parameters
        ----------
        message : data_objects.Message
            Message object read by the bot.
        """
        pass

    @abstractmethod
    def get_commands(self) -> list:
        """
        Returns a list of dict's mapping a str to a callback method.

        For example: When returning a list containing [{"command", self.method}],
        anytime a user types the word "command" the self.method method will be called.

        See also the plugin_manager.py message_callback method for how this list is
        mapped to plugin's and callback methods.
        """
        return [{"", None}]

    @abstractmethod
    def get_name(self) -> str:
        """
        The name of the plugin.
        :returns: str - The name of the plugin.
        """
        return ""

    @abstractmethod
    def get_help(self) -> str:
        """
        Information on what the plugin does.
        :returns: str - A verbose manual on the functionality of the plugin.
        """
        return ""
