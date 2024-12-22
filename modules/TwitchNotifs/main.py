"""
This is a module that checks if some Twitch streamer is live.
"""


import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
from source.settings import CONFIGS_DIRECTORY


class TwitchNotifsModule(commands.Cog):
    """
    This is an example module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        self.config_path: str = f"{CONFIGS_DIRECTORY}/twitchnotifs.json"
        self.module_config: dict[str, int] | None = None
        self.guild_config: list[dict[str, str | int | list]] | None = None

        self.load_configs()

    def load_configs(self) -> None:
        """
        Loads 'twitchnotifs.json' config file
        """

        with open(self.config_path, "r", encoding="utf-8") as file:
            config = json.loads(file.read())
            self.module_config = config["config"]
            self.guild_config = config["guild_config"]

        self.check.change_interval(seconds=self.module_config["update_interval"])

    @tasks.loop(minutes=1)
    async def check(self) -> None:
        """
        Check every 'update_interval' for a new stream
        """


async def setup(client: commands.Bot) -> None:
    await client.add_cog(TwitchNotifsModule(client))
