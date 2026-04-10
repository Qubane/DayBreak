"""
Module for preventing spam bots
"""


import hashlib
import discord
import logging
import aiosqlite
from datetime import datetime
from dataclasses import dataclass
from discord import app_commands
from discord.ext import commands, tasks
from source.configs import *
from source.databases import *


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

        # start task
        self.delete_abandoned.start()

    async def on_cleanup(self):
        """
        Gets called when the bot is exiting
        """

    async def on_ready(self):
        """
        When the module is loaded
        """

    @tasks.loop(minutes=5)
    async def delete_abandoned(self) -> None:
        """
        Delete old messages
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

        # append new message
        self.user_statistics[message.author.id].append(message)

        # compute message hash
        original_message_hash = self.compute_message_content_hash(message)

        # compare to other messages
        repeats = 0
        channels = set()
        for old_message in self.user_statistics[message.author.id]:
            message_hash = self.compute_message_content_hash(old_message)
            if original_message_hash == message_hash:
                repeats += 1
                channels.add(old_message.channel.id)

        # if repeat count and channel count is more than or equal to 4
        if repeats >= 4 and len(channels) >= 4:
            await message.author.timeout()

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
