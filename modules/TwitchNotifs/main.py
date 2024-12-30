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
from modules.TwitchNotifs.fetcher import get_live, get_title


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
        # 'channel_name': True/False (live/offline)
        self.channels_live: dict[str, bool] = dict()
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

    async def fetch_channel_states(self) -> dict[str, bool]:
        """
        Checks all channels for their current state (live / offline)
        :return: 'name': True/False
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
                return await get_live(channel_name)

        response = await asyncio.gather(
            *[check_coro(channel) for channel in channels])

        # zip 'channel': 'isLive?' together & return
        return {name: live for name, live in zip(channels, response)}

    @tasks.loop(minutes=1)
    async def check(self) -> None:
        """
        Check every 'update_interval' for a new stream
        """

        # check if we initialized current state of channels
        if not self.channels_init:
            self.channels_init = True
            self.channels_live = await self.fetch_channel_states()
            return

        # fetch current state
        new_channels_live = await self.fetch_channel_states()

        # go through all guilds
        for guild_config in self.guild_config:
            notification_channel = self.client.get_channel(guild_config["notifications_channel_id"])
            role_ping = f"<@&{guild_config["role_id"]}>"

            # check every configured twitch channel
            for channel in guild_config["channels"]:
                # if a channel is live, and it wasn't before -> make a notification
                if new_channels_live[channel] != self.channels_live[channel] and new_channels_live[channel] is True:
                    await self.make_announcement(
                        # required args
                        discord_channel=notification_channel,
                        formatting=guild_config["format"],
                        # keyword args
                        role_mention=role_ping,
                        channel_name=channel,
                        stream_description=await get_title(channel),
                        stream_url=f"https://www.twitch.tv/{channel}")

        # update channel states
        self.channels_live = new_channels_live

    @staticmethod
    async def make_announcement(
            discord_channel: discord.TextChannel,
            formatting: dict,
            **kwargs
    ) -> None:
        """
        Makes an announcement
        :param discord_channel: news channel
        :param formatting: formatting for notification
        :key role_mention: role to mention (from docs)
        :key channel_name: twitch channel name (from docs)
        :key stream_description: twitch stream description (from docs)
        :key stream_url: twitch stream url (from docs)
        """

        # format text and embed
        notification_text = formatting["text"].format(**kwargs)
        notification_embed = discord.Embed(
            title=formatting["embed"]["title"].format(**kwargs),
            description=formatting["embed"]["description"].format(**kwargs),
            url=formatting["embed"]["url"].format(**kwargs),
            color=discord.Color.from_str(formatting["embed"]["color"]))
        notification_embed.set_author(name=formatting["embed"]["author"])

        # send message
        msg_ctx = await discord_channel.send(
            content=notification_text,
            embed=notification_embed)

        # publish message if inside news channel
        if discord_channel.is_news():
            await msg_ctx.publish()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(TwitchNotifsModule(client))
