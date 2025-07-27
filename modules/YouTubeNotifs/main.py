"""
This is a module that adds the ability for the bot to send notifications
about new videos/streams made by different authors.
"""


import json
import asyncio
import discord
import logging
from discord import app_commands
from discord.ext import commands, tasks
from source.configs import *
from source.notifications import make_announcement
from modules.YouTubeNotifs.fetcher import Fetcher, Media, Channel


class YouTubeNotifsModule(commands.Cog):
    """
    This is YouTube notifications module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client: commands.Bot = client
        self.module_name: str = "YouTubeNotifs"

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        self.module_config: ModuleConfig = ModuleConfig(self.module_name)
        self.guild_config: GuildConfigCollection = GuildConfigCollection(self.module_name)

        # youtube channels
        # {"channel_id": [Video(...), Video(...), ...]}
        self.channels_videos: dict[str, list[Media]] = dict()

        # "channel_id": Channel(...)
        self.channels: dict[str, Channel] = dict()

        self.check.change_interval(seconds=self.module_config.update_interval)
        self.check.start()

    async def on_cleanup(self):
        """
        Gets called when the bot is exiting
        """

    async def on_ready(self):
        """
        Fetch latest uploaded videos
        """

        # try to fetch videos
        while True:
            try:
                self.channels_videos = await self.retrieve_channel_videos()
                break
            except NotImplementedError:  # in case of error
                await asyncio.sleep(5)

        # thread semaphore
        sem = asyncio.Semaphore(self.module_config.threads)

        async def coro(_channel_id):
            async with sem:
                return await Fetcher.fetch_channel_info(_channel_id)

        # fetch and write results
        results = await asyncio.gather(*[coro(x) for x in self.channels_videos.keys()])
        self.channels = {channel_id: channel for channel_id, channel in zip(self.channels_videos.keys(), results)}

    async def retrieve_channel_videos(self, amount: int | None = None) -> dict[str, list[Media]]:
        """
        Fetches videos from all configured to be logged YT channels
        :param amount: amount of videos to fetch (default - config.fetching_window)
        :return: dict of channel_id -> list of videos by that channel
        """

        # if amount was not provided, use value from config
        if amount is None:
            amount = self.module_config.fetching_window

        # fetch all logged YT channels
        channel_ids = set()
        for guild_config in self.guild_config:
            channel_ids.update(guild_config.channels)

        # fetch videos from all configured YT channels
        sem = asyncio.Semaphore(self.module_config.threads)

        async def coro(_channel_id):
            async with sem:
                return await Fetcher.fetch_videos(_channel_id, amount)

        # fetch videos
        result = await asyncio.gather(*[coro(x) for x in channel_ids])

        # create a dictionary with channel id pointing to list of fetched videos
        channel_dict = {cid: videos for cid, videos in zip(channel_ids, result)}

        # return channel dict
        return channel_dict

    @tasks.loop(minutes=1)
    async def check(self) -> None:
        """
        Checks every 'update_interval' for a new video/stream
        """

        # new channels dictionary
        try:
            new_channels = await self.retrieve_channel_videos()
        except NotImplementedError:  # in case of error
            return

        # check every guild
        for guild_config in self.guild_config:
            notification_channel = self.client.get_channel(guild_config.notifications_channel_id)
            video_role_ping = f"<@&{guild_config.video_role_id}>"
            # stream_role_ping = f"<@&{guild_config['stream_role_id']}>"  # unused

            # check every YT channel
            for channel_id in guild_config.channels:
                # check every new video against old videos
                # don't check last new video to prevent old videos to be considered new (ex. deleted video)
                for new_video in new_channels[channel_id][:-self.module_config.checking_window_offset]:
                    # if new video is not in old videos, then make an announcement
                    if new_video not in self.channels_videos[channel_id]:
                        keywords = self.return_keywords_dict(
                            role_mention=video_role_ping,
                            channel_name=self.channels[channel_id].title,
                            channel_url=f"https://www.youtube.com/{self.channels[channel_id].custom_url}",
                            channel_thumbnail_url=self.channels[channel_id].thumbnails.high.url,
                            channel_country=self.channels[channel_id].country,
                            video_url=new_video.url,
                            video_title=new_video.title,
                            video_description=new_video.description,
                            video_thumbnail_url=new_video.thumbnails.high.url,
                            video_publish_date=new_video.published_at.__str__())

                        await make_announcement(
                            channel=notification_channel,
                            config=guild_config.format,
                            keywords=keywords)

        # reassign new_channels to self.channels
        self.channels_videos = new_channels

    @staticmethod
    def return_keywords_dict(
            role_mention: str,
            channel_name: str,
            channel_url: str,
            channel_thumbnail_url: str,
            channel_country: str,
            video_url: str,
            video_title: str,
            video_description: str,
            video_thumbnail_url: str,
            video_publish_date: str
    ) -> dict:
        """
        Returns a dict with filled keywords.
        Docs found from 'configs/youtubenotifs.md'
        """

        return {
            "role_mention": role_mention,
            "channel_name": channel_name,
            "channel_url": channel_url,
            "channel_thumbnail_url": channel_thumbnail_url,
            "channel_country": channel_country,
            "video_url": video_url,
            "video_title": video_title,
            "video_description": f"{video_description[:60]}..." if video_description is not None else None,
            "video_thumbnail_url": video_thumbnail_url,
            "video_publish_date": video_publish_date}


async def setup(client: commands.Bot) -> None:
    await client.add_cog(YouTubeNotifsModule(client))
