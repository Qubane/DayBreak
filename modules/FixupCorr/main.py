"""
This is module that corrects certain links.
ex. `https://x.com/...` to `https://fixupx.com/...`

NOTE: in the future, it should create own embeds instead of relying on other websites
"""


import discord
import logging
from discord import app_commands
from discord.ext import commands, tasks
from source.configs import *
from source.databases import *


class FixupCorrModule(commands.Cog):
    """
    This is an FixupCorr module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client: commands.Bot = client
        self.module_name: str = "FixupCorr"

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        # self.module_config: ModuleConfig = ModuleConfig(self.module_name)  # per module config
        self.guild_configs: GuildConfigCollection = GuildConfigCollection(self.module_name)  # per guild config

    async def on_cleanup(self):
        """
        Gets called when the bot is exiting
        """

    async def on_ready(self):
        """
        When the module is loaded
        """

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        """
        Message listener. Checks messages for links and processes them accordingly
        """


async def setup(client: commands.Bot) -> None:
    await client.add_cog(FixupCorrModule(client))
