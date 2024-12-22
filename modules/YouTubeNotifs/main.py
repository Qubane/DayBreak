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
from modules.YouTubeNotifs.fetcher import Fetcher, Video, Channel


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
        self.channels_videos: dict[str, list[Video]] = dict()

        # "channel_id": Channel(...)
        self.channels: dict[str, Channel] = dict()
        self.channels_init: bool = False

        self.load_configs()
        self.check.start()

    def load_configs(self) -> None:
        """
        Loads 'youtubenotifs.json' config file
        """

        with open(self.config_path, "r", encoding="utf-8") as file:
            config = json.loads(file.read())
            self.module_config = config["config"]
            self.guild_config = config["guild_config"]

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
            channel_ids.update(guild_config["channels"])

        # fetch videos from all configured YT channels
        channel_dict = dict()
        for channel_id in channel_ids:
            channel_dict[channel_id] = await Fetcher.fetch_videos(channel_id, amount)

        # return channel dict
        return channel_dict

    @tasks.loop(minutes=1)
    async def check(self) -> None:
        """
        Checks every 10 minutes for a new video/stream
        """

        # if channels list is not init, initialize it
        if not self.channels_init:
            self.channels_init = True
            self.channels_videos = await self.retrieve_channel_videos()
            self.channels = {
                channel_id: await Fetcher.fetch_channel_info(channel_id) for channel_id in self.channels_videos.keys()}

            # no need to continue, because we just fetched 'the newest' videos
            return

        # new channels dictionary
        new_channels = await self.retrieve_channel_videos()

        # check every guild
        for guild_config in self.guild_config:
            notification_channel = self.client.get_channel(guild_config["notifications_channel_id"])
            notification_format = guild_config["format"]
            video_role_ping = f"<@&{guild_config['video_role_id']}>"
            # stream_role_ping = f"<@&{guild_config['stream_role_id']}>"  # unused

            # check every YT channel
            for channel_id in guild_config["channels"]:
                # check every new video against old videos
                # don't check last new video to prevent old videos to be considered new (ex. deleted video)
                for new_video in new_channels[channel_id][:-1]:
                    # if new video is not in old videos, then make an announcement
                    if new_video not in self.channels_videos[channel_id]:
                        msg = notification_format.format(
                            role_mention=video_role_ping,
                            channel_name=self.channels[channel_id].title,
                            channel_url=f"https://www.youtube.com/{self.channels[channel_id].custom_url}",
                            channel_thumbnail_url=self.channels[channel_id].thumbnails["default"].url,
                            channel_country=self.channels[channel_id].country,
                            video_url=f"https://youtu.be/{new_video.id}",
                            video_title=new_video.title,
                            video_description=new_video.description,
                            video_thumbnail_url=new_video.thumbnails["default"].url,
                            video_publish_date=new_video.published_at)
                        await notification_channel.send(msg)

        # reassign new_channels to self.channels
        self.channels_videos = new_channels


async def setup(client: commands.Bot) -> None:
    await client.add_cog(YouTubeNotifsModule(client))
