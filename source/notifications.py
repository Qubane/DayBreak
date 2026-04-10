import discord
import logging
from datetime import timedelta
from discord.ext import commands
from source.configs import *


def format_string(string: str | None, *args, **kwargs) -> str | None:
    """
    Formats a string and if the input is None -> returns
    :param string: string to format
    :param args: formatting arguments
    :param kwargs: formatting keyword arguments
    :return: formatted string or None
    """

    if string is None:
        return
    return string.format(*args, **kwargs)


async def make_announcement(
        channel: discord.TextChannel,
        config: GuildConfig,
        keywords: dict,
        publish: bool = True
) -> None:
    """
    Makes a formatted announcement in a given channel
    :param channel: channel for the announcement message
    :param config: formatting data
    :param keywords: configured keywords
    :param publish: if True, and is in news channel, the message will be published
    """

    # text
    text = format_string(config.text, **keywords)

    # embed
    embed = discord.Embed(
        title=format_string(config.embed.body.title, **keywords),
        description=format_string(config.embed.body.description, **keywords),
        url=format_string(config.embed.body.url, **keywords),
        color=discord.Color.from_str(config.embed.body.color))
    embed.set_image(
        url=format_string(config.embed.thumbnail, **keywords))
    embed.set_author(
        name=format_string(config.embed.author.name, **keywords),
        url=format_string(config.embed.author.url, **keywords),
        icon_url=format_string(config.embed.author.icon_url, **keywords))
    for field_config in config.embed.fields:
        embed.add_field(
            name=format_string(field_config.name, **keywords),
            value=format_string(field_config.value, **keywords))

    # sending and publishing
    message_context = await channel.send(content=text, embed=embed)

    if publish and channel.is_news():
        await message_context.publish()


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


async def member_timeout(
        member: discord.Member,
        duration: timedelta,
        reason: str,
        author: discord.Member,
        logger: logging.Logger | None = None):
    """
    Timeout and notify member
    :param member: member to timeout
    :param duration: timeout until
    :param reason: reason for timeout
    :param author: punishment author
    :param logger: logger
    """

    # try timeout
    try:
        await member.timeout(duration, reason=reason)
    except discord.Forbidden:
        raise commands.MissingPermissions(
            ["moderate_members"],
            "Bot is missing permissions")

    # embed that will be sent to punished user
    punished_embed = discord.Embed(
        title="Timeout!",
        description="You were put on a timeout",
        color=discord.Color.red())
    punished_embed.add_field(name="Reason", value=reason, inline=True)
    punished_embed.add_field(name="Duration", value=duration.__str__())
    punished_embed.set_author(name=author.name, icon_url=author.display_avatar.url)

    # try notify user
    await try_notify(member, punished_embed, logger)


async def member_kick(
        member: discord.Member,
        reason: str,
        author: discord.Member,
        logger: logging.Logger | None = None):
    """
    Kick and notify member
    :param member: member to kick
    :param reason: reason for kick
    :param author: punishment author
    :param logger: logger
    """

    # embed that will be sent to punished user
    punished_embed = discord.Embed(
        title=f"You were kicked from {author.guild.name}",
        color=discord.Color.red())
    punished_embed.add_field(name="Reason", value=reason, inline=True)
    punished_embed.set_author(name=author.name, icon_url=author.display_avatar.url)

    # try notify user
    await try_notify(member, punished_embed, logger)

    # try kick
    await member.kick(reason=reason)


async def member_ban(
        member: discord.Member,
        delete_within_days: int,
        reason: str,
        author: discord.Member,
        logger: logging.Logger | None = None):
    """
    Ban and notify member
    :param member: member to ban
    :param delete_within_days: delete messages within given number of days
    :param reason: reason for ban
    :param author: punishment author
    :param logger: logger
    """

    # embed that will be sent to punished user
    punished_embed = discord.Embed(
        title=f"You were banned from {author.guild.name}",
        color=discord.Color.red())
    punished_embed.add_field(name="Reason", value=reason, inline=True)
    punished_embed.set_author(name=author.name, icon_url=author.display_avatar.url)

    # try notify user
    await try_notify(member, punished_embed, logger)

    # try kick
    await member.ban(delete_message_days=delete_within_days, reason=reason)
