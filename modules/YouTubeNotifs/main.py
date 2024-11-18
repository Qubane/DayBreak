"""
This is a module that adds the ability for the bot to send notifications
about new videos/streams made by different authors.
"""


import discord
from discord import app_commands
from discord.ext import commands, tasks


class YouTubeNotifsModule(commands.Cog):
    """
    This is YouTube notifications module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        self.check.start()

    @tasks.loop(minutes=10)
    async def check(self):
        """
        Checks every 10 minutes for a new video/stream
        """


async def setup(client: commands.Bot) -> None:
    await client.add_cog(YouTubeNotifsModule(client))
