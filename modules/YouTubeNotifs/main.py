"""
This is a module that adds the ability for the bot to send notifications
about new videos/streams made by different authors.
"""


import discord
from discord import app_commands
from discord.ext import commands, tasks
from modules.YouTubeNotifs.fetcher import Fetcher


class YouTubeNotifsModule(commands.Cog):
    """
    This is YouTube notifications module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        self.yt_notifs_config: list[dict[str, str | int | list]] | None = None

        self.check.start()

    def load_configs(self) -> None:
        """
        Loads 'youtubenotifs.json' config file
        """

    @tasks.loop(minutes=10)
    async def check(self) -> None:
        """
        Checks every 10 minutes for a new video/stream
        """


async def setup(client: commands.Bot) -> None:
    await client.add_cog(YouTubeNotifsModule(client))
