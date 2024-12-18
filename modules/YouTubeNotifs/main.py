"""
This is a module that adds the ability for the bot to send notifications
about new videos/streams made by different authors.
"""


import json
import asyncio
import discord
from discord import app_commands
from discord.ext import commands, tasks
from source.settings import CONFIGS_DIRECTORY
from modules.YouTubeNotifs.fetcher import Fetcher, Video


class YouTubeNotifsModule(commands.Cog):
    """
    This is YouTube notifications module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        self.config_path: str = f"{CONFIGS_DIRECTORY}/youtubenotifs.json"
        self.module_config: dict[str, str | int] | None = None
        self.guild_config: list[dict[str, str | int | list]] | None = None

        # youtube channels
        # {"channel_id": [Video(...), Video(...), ...]}
        self.channels: dict[str, list[Video]] = dict()
        self.channels_init: bool = False

        self.load_configs()
        self.check.start()

    def load_configs(self) -> None:
        """
        Loads 'youtubenotifs.json' config file
        """

        with open(self.config_path, "r", encoding="utf-8") as file:
            config = json.loads(file.read())
            self.module_config = config["configs"]
            self.guild_config = config["guild_configs"]

        self.check.change_interval(seconds=self.module_config["update_interval"])

    async def initialize_channels(self) -> None:
        """
        Initializes channels dictionary 'self.channels'
        """

        # fetch all logged yt channels
        channel_ids = set()
        for guild_config in self.guild_config:
            channel_ids.update(guild_config["channels"])

        # initialize all yt channels with videos
        for channel_id in channel_ids:
            self.channels[channel_id] = await Fetcher.fetch_videos(channel_id, self.module_config["fetching_window"])

    @tasks.loop(minutes=10)
    async def check(self) -> None:
        """
        Checks every 10 minutes for a new video/stream
        """

        # if channels list is not init, initialize it
        if not self.channels_init:
            self.channels_init = True
            await self.initialize_channels()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(YouTubeNotifsModule(client))
