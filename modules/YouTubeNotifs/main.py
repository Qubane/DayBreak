"""
This is a module that adds the ability for the bot to send notifications
about new videos/streams made by different authors.
"""
import asyncio
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
from source.settings import CONFIGS_DIRECTORY
from modules.YouTubeNotifs.fetcher import Fetcher, Channel


class YouTubeNotifsModule(commands.Cog):
    """
    This is YouTube notifications module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        self.config_path: str = f"{CONFIGS_DIRECTORY}/youtubenotifs.json"
        self.module_config: dict[str, str | int] | None = None
        self.guild_config: list[dict[str, str | int | list]] | None = None

        self.channels: dict[str, Channel] | None = None
        self.channels_fetched: bool = False

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

        channel_ids = []
        for guild in self.guild_config:
            for channel_id in guild["channels"]:
                if channel_id not in channel_ids:
                    channel_ids.append(channel_id)
        self.channels = {x: Channel(x) for x in channel_ids}

    @tasks.loop(minutes=10)
    async def check(self) -> None:
        """
        Checks every 10 minutes for a new video/stream
        """

        # first time run. This is awful, I hate this so much
        if not self.channels_fetched:
            await asyncio.gather(*[x.fetch_changes() for x in self.channels.values()])
            self.channels_fetched = True

        for guild in self.guild_config:
            news_channel = self.client.get_channel(guild["notifs_id"])
            changes_list = await asyncio.gather(
                *[self.fetch_channel_changes(channel_id) for channel_id in guild["channels"]])

            for change in changes_list:
                channel_id = change[0]
                channel_changes = change[1]
                # TODO: add different pings, depending on uploaded content (video or stream)
                for video_id in channel_changes:
                    message = guild["format"].format(
                        role_mention=f"<@&{guild['video_role']}>",
                        channel_name=self.channels[channel_id].channel_name,
                        video_url=f"https://www.youtube.com/watch?v={video_id}")
                    await news_channel.send(message)

    async def fetch_channel_changes(self, channel_id: str) -> tuple[str, list[str]]:
        """
        Similar to 'Channel.fetch_changes()', except it now includes channel id in return
        :param channel_id: channel id
        :return: (channel_id, [video_id, video_id, ...])
        """

        return channel_id, await self.channels[channel_id].fetch_changes()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(YouTubeNotifsModule(client))
