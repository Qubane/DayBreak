"""
This module adds simple utils commands.
Commands such as: latency; reload_cog; etc
"""


import asyncio
import discord
import logging
from datetime import timedelta
from discord import app_commands
from discord.ext import commands


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
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

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
            raise commands.MissingPermissions(["moderate_members"])

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

        # check if the bot has privileges to time out the other user
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

        # kick the user
        await user.ban(delete_message_days=days, reason=reason)

        # make success message to command caller
        author_embed = discord.Embed(title="Success!",
                                     description=f"User {user.mention} was banned from the server",
                                     color=discord.Color.green())

        # send the message
        await interaction.response.send_message(embed=author_embed, ephemeral=True)

    # @commands.command(name="exec")
    # @commands.has_permissions(administrator=True)
    # @commands.is_owner()
    # async def exec(
    #         self,
    #         ctx: commands.Context,
    #         *,
    #         code: str = ""
    # ) -> None:
    #     """
    #     Executes python code
    #     """
    #
    #     # silent mode (don't print anything in response)
    #     silent = False
    #     if code[0] == "s":
    #         silent = True
    #
    #     code = code[code.find("\n"):-3].replace("\n", f"\n{' ' * 4}")
    #     try:
    #         exec(f"async def __ex(self, ctx): {code}")
    #         result = str(await locals()["__ex"](self, ctx))
    #
    #         embed = discord.Embed(
    #             title="Success!",
    #             description=result if len(result) <= 1990 else result[:1990],
    #             color=discord.Color.green())
    #     except Exception as e:
    #         embed = discord.Embed(
    #             title=f"Error: {e.__class__.__name__}",
    #             description=e.__str__(),
    #             color=discord.Color.red())
    #
    #     if not silent:
    #         await ctx.send(embed=embed)
    #     else:
    #         await ctx.message.delete()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(UtilsModule(client))
