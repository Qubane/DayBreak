"""
This is a module that checks if some Twitch streamer is live.
"""
import json
import asyncio
import logging
from discord import app_commands
from discord.ext import commands, tasks
from source.settings import CONFIGS_DIRECTORY
from source.notifications import make_announcement
from modules.TwitchNotifs.fetcher import Fetcher, Stream


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
        self.update_key.start()

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

    @tasks.loop(hours=24)
    async def update_key(self) -> None:
        """
        Updates a key every 24 hours
        """

        await Fetcher.fetch_access_token()

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
        channels_live = await self.fetch_streams()

        # go through all guilds
        for guild_config in self.guild_config:
            notification_channel = self.client.get_channel(guild_config["notifications_channel_id"])
            role_ping = f"<@&{guild_config["role_id"]}>"

            # check every configured twitch channel
            for channel in guild_config["channels"]:
                # if channel is live, and it wasn't before, make a notification
                if channels_live[channel] is not None and self.channels_live[channel] is None:
                    stream = channels_live[channel]
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

                    await make_announcement(
                        channel=notification_channel,
                        config=guild_config["format"],
                        keywords=keywords)

        # update channel states
        self.channels_live = channels_live

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

    @commands.command(name="test-twitch-announcement")
    @commands.has_permissions(administrator=True)
    async def debug_announcement_test(
            self,
            ctx: commands.Context
    ) -> None:
        """
        Checks for properly configured announcements
        """

        # test current guild config
        for guild_config in self.guild_config:
            if guild_config["guild_id"] == ctx.guild.id:
                break
        else:
            raise commands.CommandError("this server doesn't have notifications configured")

        keywords = self.return_keywords_dict(
            role_mention="role_mention",
            channel_name="channel_name",
            stream_url="https://localhost/",
            stream_title="stream_title",
            stream_thumbnail_url="https://static-cdn.jtvnw.net/previews-ttv/live_user_the_almighty_cube-640x360.jpg",
            stream_language="stream_language",
            stream_start_date="stream_start_date",
            stream_game_name="stream_game_name",
            stream_tags=["tag1", "tag2", "tag3"],
            stream_nsfw=True)

        await make_announcement(
            ctx.channel,
            guild_config["format"],
            keywords=keywords,
            publish=False)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(TwitchNotifsModule(client))
