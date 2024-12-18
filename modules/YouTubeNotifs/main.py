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

    async def retrieve_channel_videos(self, amount: int | None = None) -> dict[str, list[Video]]:
        """
        Fetches videos from all configured to be logged YT channels
        :param amount: amount of videos to fetch (default - config.fetching_window)
        :return: dict of channel_id -> list of videos by that channel
        """

        if amount is None:
            amount = self.module_config["fetching_window"]

        # fetch all logged YT channels
        channel_ids = set()
        for guild_config in self.guild_config:
            channel_ids.update(guild_config["youtube_channels"])

        # fetch videos from all configured YT channels
        channel_dict = dict()
        for channel_id in channel_ids:
            channel_dict[channel_id] = await Fetcher.fetch_videos(channel_id, amount)

        # return channel dict
        return channel_dict

    @tasks.loop(minutes=10)
    async def check(self) -> None:
        """
        Checks every 10 minutes for a new video/stream
        """

        # if channels list is not init, initialize it
        if not self.channels_init:
            self.channels_init = True
            self.channels = await self.retrieve_channel_videos()

            # no need to continue, because we just fetched 'the newest' videos
            return

        # new channels dictionary
        new_channels = await self.retrieve_channel_videos()

        # check every guild
        for guild_config in self.guild_config:
            notification_channel = self.client.get_channel(guild_config["notifications_channel_id"])
            notification_format = guild_config["format"]
            video_role_ping = f"<@&{guild_config['video_role_id']}>"
            stream_role_ping = f"<@&{guild_config['stream_role_id']}>"

            # check every YT channel
            for channel_id in guild_config["youtube_channels"]:
                # check every new video against old videos
                # don't check last new video to prevent old videos to be considered new (ex. deleted video)
                for new_video in new_channels[channel_id][:-1]:
                    # if new video is not in old videos, then make an announcement
                    if new_video.id not in self.channels[channel_id]:
                        # TODO: make announcement
                        break

        # reassign new_channels to self.channels
        self.channels = new_channels


async def setup(client: commands.Bot) -> None:
    await client.add_cog(YouTubeNotifsModule(client))
