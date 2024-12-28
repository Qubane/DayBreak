"""
This is module that implements memberships.
All users on a configured server must have a membership
All newly joined users will be given a membership role
"""


import json
import asyncio
import discord
import logging
from discord import app_commands
from discord.ext import commands
from source.settings import CONFIGS_DIRECTORY


class Memberships(commands.Cog):
    """
    Membership module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        self.config_path: str = f"{CONFIGS_DIRECTORY}/memberships.json"
        self.guild_config: dict[int, int] | None = None

        # load
        self.load_config()

    def load_config(self) -> None:
        """
        Loads module configs
        """

        with open(f"{CONFIGS_DIRECTORY}/memberships.json", "r", encoding="ascii") as f:
            guild_config = json.loads(f.read())
        self.guild_config = {int(x): int(y) for x, y in guild_config.items()}

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        Discord event, when a new member joins a guild
        :param member: guild member
        """

        if member.guild.id not in self.guild_config:
            return

        await self.give_membership(member)

    async def give_membership(self, member: discord.Member) -> None:
        """
        Grants members server membership
        """

        # check if user has the role
        role_id = self.guild_config[member.guild.id]
        if role_id in member._roles:
            return

        # add role, if missing
        await member.add_roles(member.guild.get_role(role_id))

    async def check_all_memberships(self) -> None:
        """
        Checks all users in all guilds for membership presence
        """

        sem = asyncio.Semaphore(20)

        async def coro(_member):
            async with sem:
                await self.give_membership(_member)
        for guild in self.client.guilds:
            if guild.id not in self.guild_config:
                self.logger.warning(f"Memberships not configured for '{guild.name}' [{guild.id}]")
                continue

            await asyncio.gather(*[coro(mem) for mem in guild.members])


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Memberships(client))
