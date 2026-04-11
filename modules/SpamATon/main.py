"""
Module for preventing spam bots
"""


import hashlib
import discord
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
            delete_within_days=1,
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
            if delta.seconds > self.module_config.message_window:
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

        # if repeat count and channel count is more than allowed
        if repeats >= self.module_config.repeat_limit and len(channels) >= self.module_config.repeat_limit:
            self_member = self.client.get_guild(message.guild.id).get_member(self.client.user.id)

            # create notification
            # fetch channel id
            channel = self.client.get_channel(self.guild_config[message.guild.id].notification_channel_id)

            # get questionable content
            message_content = message.content + "\n" + "\n".join(x.url for x in message.attachments)
            message_content = message_content[:1000]

            # create embed
            embed = discord.Embed(
                title="Spam bot detected",
                description=f"Possible spam account {message.author.mention}",
                color=discord.Color.orange())
            embed.add_field(name="Message content", value=message_content, inline=False)

            # create 2 buttons action
            if has_privilege(self_member, message.author):
                action = TimeoutUserAction(
                    timeout_member=message.author,
                    self_user=self_member,
                    logger=self.logger)
            else:
                action = None
                embed.description += "; Manual action required, bot lacks permissions"

            # send message
            await channel.send(embed=embed, view=action)

            # timeout user and delete past messages
            if has_privilege(self_member, message.author):
                await member_timeout(
                    member=message.author,
                    duration=timedelta(minutes=self.module_config.timeout_duration),
                    reason="spam",
                    author=self_member,
                    logger=self.logger)

                # delete spam messages
                for old_message in user_statistic:
                    await old_message.delete()

            # clear messages
            user_statistic.clear()

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
