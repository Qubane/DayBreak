"""
This module adds simple utils commands.
Commands such as: latency; reload_cog; etc
"""


import asyncio
import discord
import logging
from datetime import datetime, timedelta
from discord import app_commands
from discord.ext import commands, tasks
from source.configs import *
from source.databases import *


def has_privilege(caller: discord.Member, user: discord.Member) -> bool:
    """
    Compares privileges of 2 users. If 'caller' has higher privilege, returns True
    :param caller: first user
    :param user: second user
    :return: True when 'caller' > 'user'; otherwise False
    """

    hierarchy_check = caller.top_role > user.top_role   # if the caller's top role is above user's top role
    owner_check = caller.guild.owner == caller          # if caller is an owner

    # if either one is these are True
    positive_checks = any([hierarchy_check, owner_check])

    # if either one of these are True then the entire statement is False
    negative_checks = user.guild.owner == user          # if the user is an owner

    return positive_checks and not negative_checks


async def try_notify(user: discord.Member, embed: discord.Embed, logger: logging.Logger | None = None):
    """
    Try to notify user about something
    :param user: guild member
    :param embed: pretty embed
    :param logger: logger
    """

    # if logger was not defined
    if logger is None:
        logger = logging.getLogger(__name__)

    # try to send user a dm
    try:
        await user.send(embed=embed)

    # if it failed for these reasons, just ignore
    except (discord.HTTPException, discord.Forbidden):
        pass

    # if something else failed, print a message
    except Exception as e:
        logger.warning("An error had occurred while sending timeout message to user", exc_info=e)


class UtilsModule(commands.Cog):
    """
    This is an example module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client: commands.Bot = client
        self.module_name: str = "Utils"

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        self.module_config: ModuleConfig = ModuleConfig(self.module_name)
        self.guilds_config: GuildConfigCollection = GuildConfigCollection(self.module_name)

        # databases
        self.warns_db_handle: DatabaseHandle = DatabaseHandle(self.module_name)
        self.warns_db: aiosqlite.Connection | None = None

        # tasks
        self.check_warn_resets.start()

    async def on_cleanup(self):
        """
        Gets called when the bot is exiting
        """

        await self.warns_db_handle.close()
        self.logger.info("Database closed")

    async def on_ready(self):
        """
        When the module is loaded
        """

        # connect to database
        self.warns_db = await self.warns_db_handle.connect()
        self.logger.info("Database connected")

        # check the tables are present
        async with self.warns_db.cursor() as cur:
            cur: aiosqlite.Cursor  # help with type hinting
            guild_ids = [guild.id for guild in self.client.guilds]
            await create_table_if_not_exists(cur, guild_ids, """
                CREATE TABLE IF NOT EXISTS {table_name}(
                    UserId INTEGER PRIMARY KEY,
                    WarnCount INTEGER DEFAULT 0,
                    LastWarn INTEGER DEFAULt 0
                );""")

        # commit database changes
        await self.warns_db.commit()

    @app_commands.command(name="latency", description="shows bots latency")
    async def latency(
        self,
        interaction: discord.Interaction
    ) -> None:
        """
        This is a simple command, that shows bot latency
        """

        embed = discord.Embed(
            title="Latency",
            description=f"Bots latency is {self.client.latency * 1000:.4f} ms",
            color=discord.Color.brand_green())

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="btimeout", description="timeouts a user")
    @app_commands.checks.has_permissions(moderate_members=True)
    @app_commands.guild_only()
    @app_commands.describe(
        user="user to timeout",
        seconds="how many seconds to timeout for",
        minutes="how many minutes to timeout for",
        hours="how many hours to timeout for",
        days="how many days to timeout for",
        weeks="how many weeks to timeout for",
        reason="reason for a timeout (default is 'bad behaviour')")
    async def better_timeout(
            self,
            interaction: discord.Interaction,
            user: discord.Member,
            seconds: int = 0,
            minutes: int = 0,
            hours: int = 0,
            days: int = 0,
            weeks: int = 0,
            reason: str = "bad behaviour"
    ) -> None:
        """
        Command that will time you out.
        Code taken from 'UltraQbik/MightyOmegaBot'
        """

        # check if the bot has privileges to time out the other user
        self_member = interaction.guild.get_member(self.client.user.id)
        if not has_privilege(self_member, user):
            raise commands.MissingPermissions(
                ["moderate_members"],
                f"User {user.mention} has higher or equal privilege. Bot is missing permissions")

        # check if the command caller has the permissions to time out the other user
        if not has_privilege(interaction.user, user):
            raise commands.MissingPermissions(
                ["moderate_members"],
                f"User {user.mention} has higher or equal privilege")

        # calculate duration, and give a timeout
        duration = timedelta(seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks)

        # if total time is ~0, make 60 seconds
        if duration.total_seconds() < 0.1:
            duration = timedelta(seconds=60)

        # give timeout
        # either discord.py is being silly or discord, but "moderate_members" doesn't get computed correctly
        try:
            await user.timeout(duration, reason=reason)
        except discord.Forbidden:
            raise commands.MissingPermissions(
                ["moderate_members"],
                "Bot is missing permissions")

        # make timeout success message to command caller
        author_embed = discord.Embed(title="Success!",
                                     description=f"User {user.mention} was put on a timeout",
                                     color=discord.Color.green())

        # send the message
        await interaction.response.send_message(embed=author_embed, ephemeral=True)

        # make timeout message to user who was put on a timeout
        user_embed = discord.Embed(title="Timeout!",
                                   description="You were put on a timeout",
                                   color=discord.Color.red())
        user_embed.add_field(name="Reason", value=reason, inline=True)
        user_embed.add_field(name="Duration", value=duration.__str__())
        user_embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

        # try to notify user
        await try_notify(user, user_embed, self.logger)

    @app_commands.command(name="bkick", description="kicks a user")
    @app_commands.checks.has_permissions(kick_members=True)
    @app_commands.guild_only()
    @app_commands.describe(
        user="user to kick",
        reason="reason for a kick (default is 'bad behaviour')")
    async def better_kick(
            self,
            interaction: discord.Interaction,
            user: discord.Member,
            reason: str = "bad behaviour"
    ) -> None:
        """
        Command that will kick users
        """

        # check if the bot has privileges to time out the other user
        self_member = interaction.guild.get_member(self.client.user.id)
        if not has_privilege(self_member, user) or not self_member.guild_permissions.kick_members:
            raise commands.MissingPermissions(
                ["kick_members"],
                f"User {user.mention} has higher or equal privilege. Bot is missing permissions")

        # check if the command caller has the permissions to kick the other user
        if not has_privilege(interaction.user, user):
            raise commands.MissingPermissions(
                ["kick_members"],
                f"User {user.mention} has higher or equal privilege")

        # make message for the user who is going to be kicked out
        user_embed = discord.Embed(title="You were kicked from the server",
                                   color=discord.Color.red())
        user_embed.add_field(name="Reason", value=reason, inline=True)
        user_embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

        # try to notify user
        await try_notify(user, user_embed, self.logger)

        # kick the user
        await user.kick(reason=reason)

        # make success message to command caller
        author_embed = discord.Embed(title="Success!",
                                     description=f"User {user.mention} was kicked from the server",
                                     color=discord.Color.green())

        # send the message
        await interaction.response.send_message(embed=author_embed, ephemeral=True)

    @app_commands.command(name="bban", description="bans a user")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.guild_only()
    @app_commands.describe(
        user="user to ban",
        days="messages that will be deleted within this time",
        reason="reason for a ban (default is 'bad behaviour')")
    async def better_ban(
            self,
            interaction: discord.Interaction,
            user: discord.Member,
            days: int = 0,
            reason: str = "bad behaviour"
    ) -> None:
        """
        Command that will ban users
        """

        # check if the bot has privileges to ban the other user
        self_member = interaction.guild.get_member(self.client.user.id)
        if not has_privilege(self_member, user) or not self_member.guild_permissions.ban_members:
            raise commands.MissingPermissions(
                ["ban_members"],
                f"User {user.mention} has higher or equal privilege. Bot is missing permissions")

        # check if the command caller has the permissions to ban the other user
        if not has_privilege(interaction.user, user):
            raise commands.MissingPermissions(
                ["ban_members"],
                f"User {user.mention} has higher or equal privilege")

        # make message for the user who is going to be kicked out
        user_embed = discord.Embed(title="You were banned from the server",
                                   color=discord.Color.red())
        user_embed.add_field(name="Reason", value=reason, inline=True)
        user_embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

        # try to notify user
        await try_notify(user, user_embed, self.logger)

        # ban the user
        await user.ban(delete_message_days=days, reason=reason)

        # make success message to command caller
        author_embed = discord.Embed(title="Success!",
                                     description=f"User {user.mention} was banned from the server",
                                     color=discord.Color.green())

        # send the message
        await interaction.response.send_message(embed=author_embed, ephemeral=True)

    @tasks.loop(minutes=5)
    async def check_warn_resets(self) -> None:
        """
        Performs some kind of task
        """

        async with self.warns_db.cursor() as cur:
            cur: aiosqlite.Cursor

    @app_commands.command(name="warn", description="warns user")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.guild_only()
    @app_commands.describe(
        user="user to warn",
        reason="reason for a ban (default is 'bad behaviour')",
        silent="silently warn a user (default is False)")
    async def command_warn(
            self,
            interaction: discord.Interaction,
            user: discord.Member,
            reason: str = "bad behaviour",
            silent: bool = False
    ) -> None:
        """
        Warns a user
        """

        # check if the bot has privileges to warn / ban the other user
        self_member = interaction.guild.get_member(self.client.user.id)
        if not has_privilege(self_member, user) or not self_member.guild_permissions.ban_members:
            raise commands.MissingPermissions(
                ["ban_members"],
                f"User {user.mention} has higher or equal privilege. Bot is missing permissions")

        # check if the command caller has the permissions to warn / ban the other user
        if not has_privilege(interaction.user, user):
            raise commands.MissingPermissions(
                ["ban_members"],
                f"User {user.mention} has higher or equal privilege")

        # db cursor
        async with self.warns_db.cursor() as cur:
            cur: aiosqlite.Cursor

            # user parameters
            user_id = user.id
            table_name = f"g{interaction.guild_id}"

            # insert or ignore
            await insert_or_ignore_user(cur, table_name, user_id)

            # fetch user warns
            query = await cur.execute(f"SELECT WarnCount FROM {table_name} WHERE UserId = ?", (user_id,))
            warn_count = (await query.fetchone())[0] + 1

            # get config warn limit
            max_warn_count = self.guilds_config.get(interaction.guild_id, self.module_config).max_warn_count

            # check if user is to be banned
            is_user_banned = False
            if warn_count >= max_warn_count:
                is_user_banned = True

            # last warn timestamp
            last_warn = int(datetime.now().timestamp())

            # update warn counter
            await cur.execute(
                f"UPDATE {table_name} SET WarnCount = ?, LastWarn = ? WHERE UserId = ?",
                (warn_count, last_warn, user_id,))

            # if user is to be banned
            if is_user_banned:
                # make message for the user who is going to be kicked out
                user_embed = discord.Embed(title="You exceeded the number of warns; You have been banned",
                                           color=discord.Color.red())
                user_embed.add_field(name="Reason", value=reason, inline=True)
                user_embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

                # try to notify user
                await try_notify(user, user_embed, self.logger)

                # ban the user
                await user.ban(reason=reason)

            # if user is not banned, and silent flag is off
            elif not silent:
                # make message for the user who is going to be kicked out
                user_embed = discord.Embed(title=f"You have been given a warning. Current warn count: {warn_count}",
                                           color=discord.Color.red())
                user_embed.add_field(name="Reason", value=reason, inline=True)
                user_embed.set_author(name=interaction.user.name, icon_url=interaction.user.display_avatar.url)

                # try to notify user
                await try_notify(user, user_embed, self.logger)

        # commit changes
        await self.warns_db.commit()

        # send notification to author
        if is_user_banned:
            # make success message to command caller
            author_embed = discord.Embed(title="Success!",
                                         description=f"User {user.mention} had exceeded the number of warns, "
                                                     f"and was banned from the server",
                                         color=discord.Color.green())

            # send the message
            await interaction.response.send_message(embed=author_embed, ephemeral=True)
        else:
            # make success message to command caller
            author_embed = discord.Embed(title="Success!",
                                         description=f"User {user.mention} was given a warning. "
                                                     f"Current warn count: {warn_count}",
                                         color=discord.Color.green())

            # send the message
            await interaction.response.send_message(embed=author_embed, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(UtilsModule(client))
