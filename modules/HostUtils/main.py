"""
This module adds commands that can only by used by owner of the bot (aka bot host)
"""


import discord
import logging
from discord import app_commands
from discord.ext import commands
from source.utils import *
from source.configs import *
from source.databases import *


class HostUtilsModule(commands.Cog):
    """
    This is the HostUtils module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client: commands.Bot = client
        self.module_name: str = "HostUtils"

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        self.guild_configs: GuildConfigCollection = GuildConfigCollection(self.module_name)  # per guild config

    async def on_cleanup(self):
        """
        Gets called when the bot is exiting
        """

    @commands.command("make-announce")
    @commands.is_owner()
    async def command_make_announce(
        self,
        ctx: commands.Context,
        *,
        message: str
    ) -> None:
        """
        This is an announcement command, that is used to update people on bot news
        """

        # go through configured channels, and send notifications
        for guild_config in self.guild_configs:
            # get channel
            channel = self.client.get_channel(guild_config.bot_announcements)

            # skip undefined channels
            if channel is None:
                continue

            # send user message
            await channel.send(message)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(HostUtilsModule(client))
