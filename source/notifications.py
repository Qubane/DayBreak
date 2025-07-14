import discord
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
