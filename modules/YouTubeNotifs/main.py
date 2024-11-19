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
        self.config: list[dict[str, str | int | list]] | None = None

        self.channels: dict[str, Channel] | None = None

        self.load_configs()
        self.check.start()

    def load_configs(self) -> None:
        """
        Loads 'youtubenotifs.json' config file
        """

        with open(self.config_path, "r", encoding="utf-8") as file:
            self.config = json.loads(file.read())

        channel_ids = []
        for guild in self.config:
            for channel_id in guild["channels"]:
                if channel_id not in channel_ids:
                    channel_ids.append(channel_id)
        self.channels = {x: Channel(x) for x in channel_ids}

    @tasks.loop(minutes=10)
    async def check(self) -> None:
        """
        Checks every 10 minutes for a new video/stream
        """

        for guild in self.config:
            news_channel = self.client.get_channel(guild["notifs_id"])
            channels_changes = await asyncio.gather(
                *[self.fetch_channel_changes(channel_id) for channel_id in guild["channels"]])

            for channel_change in channels_changes:
                channel_id = channel_change[0]
                channel_changes = channel_change[1]
                for video_id in channel_changes:
                    message = guild["format"].format(
                        role_mention=f"<@&{guild['video_role']}>",
                        channel_name=self.channels[channel_id],
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
