"""
This is an example module for DayBreak bot
"""


import discord
import logging
import aiosqlite
from discord import app_commands
from discord.ext import commands, tasks
from source.configs import *
from source.databases import *


class ExampleModule(commands.Cog):
    """
    This is an example module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client: commands.Bot = client
        self.module_name: str = "Example"

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        self.module_config: ModuleConfig = ModuleConfig(self.module_name)  # per module config
        self.guild_configs: GuildConfigCollection = GuildConfigCollection(self.module_name)  # per guild config

        # databases
        self.db_handle: DatabaseHandle = DatabaseHandle(self.module_name)
        self.db: aiosqlite.Connection | None = None

        # tasks
        self.example_task.start()

    async def on_cleanup(self):
        """
        Gets called when the bot is exiting
        """

        # close the database on clean up
        await self.db_handle.close()

    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        """
        When the module is loaded
        """

        # connect to database
        self.db = await self.db_handle.connect()

    @tasks.loop(minutes=5)
    async def example_task(self) -> None:
        """
        Performs some kind of task
        """

    @app_commands.command(name="example", description="does some things")
    @app_commands.describe(
        message="Some kind of message")
    async def example(
        self,
        interaction: discord.Interaction,
        message: str
    ) -> None:
        """
        This is an example slash command
        """


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ExampleModule(client))
