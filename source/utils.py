"""
Some random utility classes
"""


import discord
from discord import app_commands
from discord.ext import commands


async def is_bot_owner(client: commands.Bot, interaction: discord.Interaction) -> bool:
    """
    Checks if the interaction was called by bot owner
    :param client: bot client
    :param interaction: app commands interaction
    :return: True if interaction was called by bot owner
    """

    return await client.is_owner(interaction.user)


async def check_bot_ownership(client: commands.Bot, interaction: discord.Interaction) -> None:
    """
    Same as 'is_bot_owner' except it raises an error instead
    :param client: bot client
    :param interaction: app commands interaction
    """

    if not (await is_bot_owner(client, interaction)):
        raise commands.MissingPermissions(
            ["bot_owner"], "You must be a host of this bot to run this command")


class DotDict(dict):
    """
    dot.notation access to dictionary attributes
    """

    def __getattr__(self, item):
        val = super().__getitem__(item)
        if isinstance(val, dict):
            return DotDict(val)
        elif isinstance(val, list):
            return [DotDict(x) if isinstance(x, (dict, list)) else x for x in val]
        else:
            return val

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
