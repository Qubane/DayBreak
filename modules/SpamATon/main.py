"""
Module for preventing spam bots
"""


import asyncio
import discord
import hashlib
import logging
import discord.ui
from datetime import datetime, timezone
from source.configs import *
from source.databases import *
from source.notifications import *
from source.utils import has_privilege


class TimeoutUserAction(discord.ui.View):
    def __init__(
            self,
            timeout_member: discord.Member,
            self_user: discord.Member,
            logger: logging.Logger | None = None):
        super().__init__()

        self.logger = logger
        self.self_user = self_user
        self.timeout_member = timeout_member

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.red)
    async def ban_button(self, interaction: discord.Interaction, button: discord.Button):
        # check permission
        if not has_privilege(interaction.user, self.timeout_member):
            raise commands.MissingPermissions(
                ["ban_members"],
                f"User {self.timeout_member.mention} has higher or equal privilege")

        # ban user
        await member_ban(
            member=self.timeout_member,
            delete_within_days=2,
            reason="Spam",
            author=interaction.user,
            logger=self.logger)

        # disable buttons
        for child in self.children:
            child.disabled = True

        # update interaction
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Remove timeout", style=discord.ButtonStyle.green)
    async def remove_timeout_button(self, interaction: discord.Interaction, button: discord.Button):
        # check permission
        if not has_privilege(interaction.user, self.timeout_member):
            raise commands.MissingPermissions(
                ["moderate_members"],
                f"User {self.timeout_member.mention} has higher or equal privilege")

        # remove timeout
        await self.timeout_member.edit(timed_out_until=None)

        # disable buttons
        for child in self.children:
            child.disabled = True

        # update interaction
        await interaction.response.edit_message(view=self)


class SpamATonModule(commands.Cog):
    """
    This is a spam bot prevention module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client: commands.Bot = client
        self.module_name: str = "SpamATon"

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        self.module_config: ModuleConfig = ModuleConfig(self.module_name)
        self.guild_config: GuildConfigCollection = GuildConfigCollection(self.module_name)

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
        Computes repeated_message content hash
        :param repeated_message: user repeated_message
        :return: md5 bytes hash
        """

        content = message.content + "".join(f"{x.size}{x.filename}" for x in message.attachments)
        return hashlib.md5(content.encode("utf-8")).digest()

    async def timeout_member(self, member: discord.Member, repeated_message: discord.Message):
        """
        Timeout the member
        """

        # get self member
        self_member = self.client.get_guild(repeated_message.guild.id).get_member(self.client.user.id)

        # timeout user and delete past messages
        if has_privilege(self_member, member):
            await member_timeout(
                member=member,
                duration=timedelta(minutes=self.module_config.timeout_duration),
                reason="possible spam",
                author=self_member,
                logger=self.logger)

            # delete spam messages
            for message in self.user_statistics[member.id]:
                await message.delete()

        # clear messages
        self.user_statistics[member.id].clear()

        # create notification
        # fetch channel id
        channel = self.client.get_channel(self.guild_config[repeated_message.guild.id].notification_channel_id)

        # get questionable content
        message_content = repeated_message.content + "\n" + "\n".join(x.url for x in repeated_message.attachments)
        message_content = message_content[:1000]

        # create embed
        embed = discord.Embed(
            title="Spam bot detected",
            description=f"Possible spam account {member.mention}",
            color=discord.Color.orange())
        embed.add_field(name="Message content", value=message_content, inline=False)

        # create 2 buttons action
        if has_privilege(self_member, member):
            action = TimeoutUserAction(
                timeout_member=member,
                self_user=self_member,
                logger=self.logger)
        else:
            action = None
            embed.description += "; Manual action required, bot lacks permissions"

        # send message
        await channel.send(embed=embed, view=action)

    async def process_message(self, repeated_message: discord.Message):
        """
        Processes the users message
        """

        # if the user wasn't in statistics
        if repeated_message.author.id not in self.user_statistics:
            self.user_statistics[repeated_message.author.id] = []

        # get user stat list
        user_statistic = self.user_statistics[repeated_message.author.id]

        # delete outdated messages
        for message in user_statistic[::]:
            if (datetime.now(timezone.utc) - message.created_at).seconds > self.module_config.message_window:
                user_statistic.remove(message)

        # append new repeated_message
        user_statistic.append(repeated_message)

        # compute repeated_message hash
        original_message_hash = self.compute_message_content_hash(repeated_message)

        # compare to other messages
        repeats = 0
        channels = set()
        for message in user_statistic:
            message_hash = self.compute_message_content_hash(message)
            if original_message_hash == message_hash:
                repeats += 1
                channels.add(message.channel.id)

        # if repeat count and channel count is more than allowed => timeout user
        if repeats >= self.module_config.repeat_limit and len(channels) >= self.module_config.repeat_limit:
            await self.timeout_member(repeated_message.author, repeated_message)

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

        # skip not configured guilds
        if message.guild.id not in self.guild_config:
            return

        # process user message
        await self.process_message(message)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SpamATonModule(client))
