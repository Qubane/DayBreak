"""
Module for preventing spam bots
"""


import hashlib
import discord
import logging
import aiosqlite
from datetime import datetime, timezone
from dataclasses import dataclass
from discord.ext import commands, tasks
from source.configs import *
from source.databases import *
from source.notifications import *


@dataclass
class UserStatistic:
    last_messages: list[discord.Message]


class SpamATonModule(commands.Cog):
    """
    This is a spam bot prevention module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client: commands.Bot = client
        self.module_name: str = "Example"

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # processing queue
        self.user_statistics: dict[int, list[discord.Message]] = {}

    async def on_cleanup(self):
        """
        Gets called when the bot is exiting
        """

    async def on_ready(self):
        """
        When the module is loaded
        """

    @staticmethod
    def compute_message_content_hash(message: discord.Message) -> bytes:
        """
        Computes message content hash
        :param message: user message
        :return: md5 bytes hash
        """

        content = message.content + "".join(f"{x.size}{x.filename}" for x in message.attachments)
        return hashlib.md5(content.encode("utf-8")).digest()

    async def process_message(self, message: discord.Message):
        """
        Processes the users message
        """

        # if the user wasn't in statistics
        if message.author.id not in self.user_statistics:
            self.user_statistics[message.author.id] = []

        # get user stat list
        user_statistic = self.user_statistics[message.author.id]

        # delete outdated messages
        for old_message in user_statistic[::]:
            delta = datetime.now(timezone.utc).replace(tzinfo=timezone.utc) - old_message.created_at
            if delta.seconds > 60:
                user_statistic.remove(old_message)

        # append new message
        user_statistic.append(message)

        # compute message hash
        original_message_hash = self.compute_message_content_hash(message)

        # compare to other messages
        repeats = 0
        channels = set()
        for old_message in user_statistic:
            message_hash = self.compute_message_content_hash(old_message)
            if original_message_hash == message_hash:
                repeats += 1
                channels.add(old_message.channel.id)

        # if repeat count and channel count is more than or equal to 3
        if repeats >= 3 and len(channels) >= 3:
            self_member = self.client.get_guild(message.guild.id).get_member(self.client.user.id)
            await member_timeout(
                member=message.author,
                duration=timedelta(minutes=30),
                reason="spam",
                author=self_member,
                logger=self.logger)
            for old_message in user_statistic:
                await old_message.delete()

    @commands.Cog.listener("on_message")
    async def on_message(self, message: discord.Message) -> None:
        """
        Append message for processing
        """

        # skip bot messages
        if message.author.bot:
            return

        # skip messages in DM's
        if isinstance(message.channel, discord.DMChannel):
            return

        # process user message
        await self.process_message(message)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SpamATonModule(client))
