"""
This is an example module for DayBreak bot
"""


import discord
from discord import app_commands
from discord.ext import commands


class ExampleModule(commands.Cog):
    """
    This is an example module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # here's an example variable
        self.example = "example"

        # here's an example path to the database
        self.db_path = "var/example_db.json"

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

        pass


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ExampleModule(client))
