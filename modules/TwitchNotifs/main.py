"""
This is a module that checks if some Twitch streamer is live.
"""
import json
import asyncio
import discord
import logging
from discord import app_commands
from discord.ext import commands, tasks
from source.settings import CONFIGS_DIRECTORY
from modules.TwitchNotifs.fetcher import Fetcher, Stream


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


class TwitchNotifsModule(commands.Cog):
    """
    This is an example module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        self.config_path: str = f"{CONFIGS_DIRECTORY}/twitchnotifs.json"
        self.module_config: dict[str, int] | None = None
        self.guild_config: list[dict] | None = None

        # channels
        # 'channel_name': Stream
        self.channels_live: dict[str, Stream | None] = dict()
        self.channels_init: bool = False

        self.load_configs()
        self.check.start()

    def load_configs(self) -> None:
        """
        Loads 'twitchnotifs.json' config file
        """

        with open(self.config_path, "r", encoding="utf-8") as file:
            config = json.loads(file.read())
            self.module_config = config["config"]
            self.guild_config = config["guild_config"]

        self.check.change_interval(seconds=self.module_config["update_interval"])

    async def fetch_streams(self) -> dict[str, Stream | None]:
        """
        Fetches streams from all logged streamers
        :return: dict of channel name to stream or none
        """

        # fetch all channels
        channels = set()
        for guild_config in self.guild_config:
            channels.update(guild_config["channels"])

        # limit concurrency
        sem = asyncio.Semaphore(self.module_config["threads"])

        # checking coroutine
        async def check_coro(channel_name):
            async with sem:
                return await Fetcher.fetch_stream_info(channel_name)

        response = await asyncio.gather(
            *[check_coro(channel) for channel in channels])

        return {key: val for key, val in zip(channels, response)}

    @tasks.loop(minutes=1)
    async def check(self) -> None:
        """
        Check every 'update_interval' for a new stream
        """

        # check if we initialized current state of channels
        if not self.channels_init:
            self.channels_init = True
            self.channels_live = await self.fetch_streams()
            return

        # fetch current state
        new_channels_live = await self.fetch_streams()

        # go through all guilds
        for guild_config in self.guild_config:
            notification_channel = self.client.get_channel(guild_config["notifications_channel_id"])
            role_ping = f"<@&{guild_config["role_id"]}>"

            # check every configured twitch channel
            for channel in guild_config["channels"]:
                # if a channel is live, and it wasn't before -> make a notification
                if new_channels_live[channel] != self.channels_live[channel] and new_channels_live[channel]:
                    stream = new_channels_live[channel]
                    keywords = self.return_keywords_dict(
                        role_mention=role_ping,
                        channel_name=stream.user_name,
                        stream_url=f"https://twitch.tv/{stream.user_login}",
                        stream_title=stream.title,
                        stream_thumbnail_url=stream.thumbnail(640, 360),
                        stream_language=stream.language,
                        stream_start_date=stream.started_at.__str__(),
                        stream_game_name=stream.game_name,
                        stream_tags=stream.tags,
                        stream_nsfw=stream.is_mature)

                    await self.make_announcement(
                        channel=notification_channel,
                        config=guild_config["format"],
                        keywords=keywords)

        # update channel states
        self.channels_live = new_channels_live

    @staticmethod
    def return_keywords_dict(
            role_mention: str,
            channel_name: str,
            stream_url: str,
            stream_title: str,
            stream_thumbnail_url: str,
            stream_language: str,
            stream_start_date: str,
            stream_game_name: str,
            stream_tags: list[str],
            stream_nsfw: bool
    ) -> dict[str, str]:
        """
        Returns a dict with filled keywords.
        Docs found from 'configs/twitchnotifs.md'
        """

        return {
            "role_mention": role_mention,
            "channel_name": channel_name,
            "stream_url": stream_url,
            "stream_title": stream_title,
            "stream_thumbnail_url": stream_thumbnail_url,
            "stream_language": stream_language,
            "stream_start_date": stream_start_date,
            "stream_game_name": stream_game_name,
            "stream_tags": stream_tags,
            "stream_nsfw": stream_nsfw}

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

    @commands.command(name="test-twitch-announcement")
    @commands.has_permissions(administrator=True)
    async def debug_announcement_test(
            self,
            ctx: commands.Context
    ) -> None:
        """
        Executes python code
        """

        keywords = self.return_keywords_dict(
            role_mention="role_mention",
            channel_name="channel_name",
            stream_url="https://localhost/",
            stream_title="stream_title",
            stream_thumbnail_url="https://yt3.googleusercontent.com/"
                                 "ZQIGQ0-2Iiwh6J-qCkBoxU5EJiQ9Nh1ZMF"
                                 "bu0m62mJLZc-xdOfTHy1rtxdFDYUk7o_ON"
                                 "HjcGmDM=s160-c-k-c0x00ffffff-no-rj",
            stream_language="stream_language",
            stream_start_date="stream_start_date",
            stream_game_name="stream_game_name",
            stream_tags=["tag1", "tag2", "tag3"],
            stream_nsfw=True)

        await self.make_announcement(
            ctx.channel,
            self.guild_config[0]["format"],
            keywords=keywords,
            publish=False)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(TwitchNotifsModule(client))
