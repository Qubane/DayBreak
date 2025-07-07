"""
This is Sentiments module for DayBreak.
It adds sentiment / positivity leaderboard.
Depending on how positive the messages are sent by user, they will be placed higher or lower on the leaderboard
It uses AI model to perform sentiment analysis on message, and update the leaderboard accordingly.
"""


import discord
import logging
from discord import app_commands
from discord.ext import commands


class SentimentsModule(commands.Cog):
    """
    Sentiments module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # here's an example path to the database
        self.db_path = "var/sentiments_leaderboard.json"

        # processing queue
        self.message_processing_queue: list[commands.Context] = []

    @app_commands.command(name="posiboard", description="positivity leaderboard")
    async def posiboard(
        self,
        interaction: discord.Interaction
    ) -> None:
        """
        Implementation for positivity leaderboard
        """

        pass

    @commands.Cog.listener()
    async def on_message(self, ctx: commands.Context) -> None:
        """
        Perform sentiment analysis on sent message
        """

        self.message_processing_queue.append(ctx)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SentimentsModule(client))
