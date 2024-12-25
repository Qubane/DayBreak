"""
This is bot utils module.
Adds the ability to load, unload and reload other modules
Always imported, and cannot be unloaded, only reloaded
"""


import discord
import logging
from discord import app_commands
from discord.ext import commands


class BotUtilsModule(commands.Cog):
    """
    Bot utils module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

    @app_commands.command(name="reload", description="reloads a module")
    @app_commands.describe(
        module="name of the module")
    async def example(
        self,
        interaction: discord.Interaction,
        module: str
    ) -> None:
        """
        This is an example slash command
        """

        pass


async def setup(client: commands.Bot) -> None:
    await client.add_cog(BotUtilsModule(client))
