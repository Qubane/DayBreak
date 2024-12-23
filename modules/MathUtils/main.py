"""
Module that adds different math related utilities.
For example, it adds LaTeX formula rendering
"""


import discord
import logging
from discord import app_commands
from discord.ext import commands


class MathUtilsModule(commands.Cog):
    """
    Math Utils module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(MathUtilsModule(client))
