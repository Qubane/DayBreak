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
from source.settings import CONFIGS_DIRECTORY
from modules.YouTubeNotifs.fetcher import Fetcher, Media, Channel


def format_string(string: str | None, *args, **kwargs) -> str | None:
    """
    Formats a string and if the input is None -> returns
    :param string: string to format
    :param args: formatting arguments
    :param kwargs: formatting keyword arguments
    :return: formatted string or None
    """

    if string is None:
        return
    return string.format(*args, **kwargs)


class YouTubeNotifsModule(commands.Cog):
    """
    This is YouTube notifications module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        self.config_path: str = f"{CONFIGS_DIRECTORY}/youtubenotifs.json"
        self.module_config: dict[str, str | int] | None = None
        self.guild_config: list[dict] | None = None

        # youtube channels
        # {"channel_id": [Video(...), Video(...), ...]}
        self.channels_videos: dict[str, list[Media]] = dict()

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

    async def retrieve_channel_videos(self, amount: int | None = None) -> dict[str, list[Media]]:
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
        sem = asyncio.Semaphore(self.module_config["threads"])

        async def coro(_channel_id):
            async with sem:
                return await Fetcher.fetch_videos(_channel_id, amount)

        result = await asyncio.gather(*[coro(x) for x in channel_ids])
        channel_dict = {cid: videos for cid, videos in zip(channel_ids, result)}

        # return channel dict
        return channel_dict

    @tasks.loop(minutes=1)
    async def check(self) -> None:
        """
        Checks every 'update_interval' for a new video/stream
        """

        # if channels list is not init, initialize it
        if not self.channels_init:
            self.channels_init = True
            self.channels_videos = await self.retrieve_channel_videos()

            sem = asyncio.Semaphore(self.module_config["threads"])

            async def coro(_channel_id):
                async with sem:
                    return await Fetcher.fetch_channel_info(_channel_id)

            results = await asyncio.gather(*[coro(x) for x in self.channels_videos.keys()])
            self.channels = {channel_id: channel for channel_id, channel in zip(self.channels_videos.keys(), results)}

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
                for new_video in new_channels[channel_id][:-self.module_config["checking_window_offset"]]:
                    # if new video is not in old videos, then make an announcement
                    if new_video not in self.channels_videos[channel_id]:
                        keywords = self.return_keywords_dict(
                            role_mention=video_role_ping,
                            channel_name=self.channels[channel_id].title,
                            channel_url=f"https://www.youtube.com/{self.channels[channel_id].custom_url}",
                            channel_thumbnail_url=self.channels[channel_id].thumbnails["default"].url,
                            channel_country=self.channels[channel_id].country,
                            video_url=f"https://youtu.be/{new_video.id}",
                            video_title=new_video.title,
                            video_description=new_video.description,
                            video_thumbnail_url=new_video.thumbnails["default"].url,
                            video_publish_date=new_video.published_at.__str__())

                        await self.make_announcement(
                            channel=notification_channel,
                            config=guild_config["format"],
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
            "video_description": video_description,
            "video_thumbnail_url": video_thumbnail_url,
            "video_publish_date": video_publish_date}

    @staticmethod
    async def make_announcement(
            channel: discord.TextChannel,
            config: dict,
            keywords: dict,
            publish: bool = True
    ) -> None:
        """
        Makes a formatted announcement in a given channel
        :param channel: channel for the announcement message
        :param config: formatting data
        :param keywords: configured keywords
        :param publish: if True, and is in news channel, the message will be published
        """

        # text
        text = format_string(config["text"], **keywords)

        # embed
        embed = discord.Embed(
            title=format_string(config["embed"]["body"]["title"], **keywords),
            description=format_string(config["embed"]["body"]["description"], **keywords),
            url=format_string(config["embed"]["body"]["url"], **keywords),
            color=discord.Color.from_str(config["embed"]["body"]["color"]))
        embed.set_image(
            url=format_string(config["embed"]["thumbnail"], **keywords))
        embed.set_author(
            name=format_string(config["embed"]["author"]["name"], **keywords),
            url=format_string(config["embed"]["author"]["url"], **keywords),
            icon_url=format_string(config["embed"]["author"]["icon_url"], **keywords))
        for field_config in config["embed"]["fields"]:
            embed.add_field(
                name=format_string(field_config["name"], **keywords),
                value=format_string(field_config["value"], **keywords))

        # sending and publishing
        message_context = await channel.send(content=text, embed=embed)

        if publish and channel.is_news():
            await message_context.publish()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(YouTubeNotifsModule(client))
