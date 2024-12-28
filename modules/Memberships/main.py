"""
This is module that implements memberships.
All users on a configured server must have a membership
All newly joined users will be given a membership role
"""


import json
import discord
import logging
from discord import app_commands
from discord.ext import commands
from source.settings import CONFIGS_DIRECTORY


class Memberships(commands.Cog):
    """
    Membership module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        self.config_path: str = f"{CONFIGS_DIRECTORY}/memberships.json"
        self.guild_config: dict[int, int] | None = None

        # load
        self.load_config()

    def load_config(self) -> None:
        """
        Loads module configs
        """


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Memberships(client))
