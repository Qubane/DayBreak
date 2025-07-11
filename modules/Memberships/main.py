"""
This is module that implements memberships.
All users on a configured server must have a membership
All newly joined users will be given a membership role
"""


import asyncio
import discord
import logging
from discord import app_commands
from discord.ext import commands
from source.configs import *


class MembershipsModule(commands.Cog):
    """
    Membership module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # config
        self.config: GuildConfigCollection = GuildConfigCollection("memberships")

        # check members
        asyncio.create_task(self.check_all_memberships())

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        Discord event, when a new member joins a guild
        :param member: guild member
        """

        if member.guild.id not in self.config:
            return

        await self.give_membership(member)

    async def give_membership(self, member: discord.Member) -> None:
        """
        Grants members server membership
        """

        # check if user has the role
        role_id = self.config[member.guild.id].member_role
        if member.get_role(role_id) is None:
            return

        # add role, if missing
        await member.add_roles(member.guild.get_role(role_id))

    async def check_all_memberships(self) -> None:
        """
        Checks all users in all guilds for membership presence
        """

        # define semaphore
        sem = asyncio.Semaphore(5)

        async def coro(_member):
            async with sem:
                await self.give_membership(_member)

        # go through all connected guilds
        for guild in self.client.guilds:
            # if guild's memberships are not configured
            if guild.id not in self.config:
                self.logger.warning(f"Memberships not configured for '{guild.name}' [{guild.id}]")
                continue

            # else try to grant everyone roles
            await asyncio.gather(*[coro(mem) for mem in guild.members])


async def setup(client: commands.Bot) -> None:
    await client.add_cog(MembershipsModule(client))
