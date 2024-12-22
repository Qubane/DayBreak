"""
This is a module that checks if some Twitch streamer is live.
"""
import asyncio
import json
import discord
from discord import app_commands
from discord.ext import commands, tasks
from source.settings import CONFIGS_DIRECTORY
from modules.TwitchNotifs.fetcher import check_live


class TwitchNotifsModule(commands.Cog):
    """
    This is an example module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        self.config_path: str = f"{CONFIGS_DIRECTORY}/twitchnotifs.json"
        self.module_config: dict[str, int] | None = None
        self.guild_config: list[dict[str, str | int | list]] | None = None

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

    @tasks.loop(minutes=1)
    async def check(self) -> None:
        """
        Check every 'update_interval' for a new stream
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
                return await check_live(channel_name)

        response = await asyncio.gather(
            *[check_coro(channel) for channel in channels])

        # zip 'channel': 'isLive?' together
        channels_live = {name: live for name, live in zip(channels, response)}

        # go through all guilds
        for guild_config in self.guild_config:
            notification_channel = self.client.get_channel(guild_config["notifications_channel_id"])
            notification_format = guild_config["format"]
            role_ping = f"<@&{guild_config["role_id"]}>"

            # check every configured twitch channel
            for channel in guild_config["channels"]:
                # if channel is live -> make a notification
                if channels_live[channel]:
                    msg = notification_format.format(
                        role_mention=role_ping,
                        channel_name=channel,  # so convenient, thx twitch
                        stream_url=f"https://www.twitch.tv/{channel}")
                    await notification_channel.send(msg)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(TwitchNotifsModule(client))
