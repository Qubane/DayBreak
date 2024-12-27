"""
This is module that implements memberships.
All users on a configured server must have a membership
All newly joined users will be given a membership role
"""


import discord
import logging
from discord import app_commands
from discord.ext import commands


class Memberships(commands.Cog):
    """
    Membership module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Memberships(client))
