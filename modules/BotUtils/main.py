"""
This is bot utils module.
Adds the ability to load, unload and reload other modules
Always imported, and cannot be unloaded, only reloaded
"""
import os
import json
import asyncio
import discord
import logging
from discord import app_commands
from discord.ext import commands
from source.settings import MODULES_DIRECTORY, CONFIGS_DIRECTORY


def make_module_path(module: str) -> str:
    """
    Makes proper paths for modules, so they could be worked with
    :param module: module name
    :return: module path
    """

    return f"{MODULES_DIRECTORY}.{module}.main"


class BotUtilsModule(commands.Cog):
    """
    Bot utils module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client
        self.module_name: str = "BotUtils"

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # modules
        self.modules_present: list[str] = list()
        self.modules_queued: list[str] = list()
        self.modules_running: list[str] = list()
        self.modules_static: list[str] = list()

        # important modules
        self.modules_static.append("ExceptionHandler")

        self.modules_queued += self.modules_static

        # static 'self.module_name' module
        self.modules_static.append(self.module_name)
        self.modules_running.append(self.module_name)  # already running

        # "guild_id": "role_id"
        self.memberships_config: dict[int, int] | None = None

        # config and module loading
        self._load_module_configs()
        self._load_modules_config()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        Discord event, when a new member joins a guild
        :param member: guild member
        """

        if member.guild.id not in self.memberships_config:
            return

        await self.give_membership(member)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        When the bot successfully connects to discord's websocket
        """

        self.logger.info("Bot connected")

        await self.load_all_queued()
        self.logger.info("All modules loaded")

        await self.client.change_presence(activity=discord.Game("A DayBreak"))

        await self.client.tree.sync()
        self.logger.info("Command tree synced")

    def _load_modules_config(self) -> None:
        """
        Loads 'self.modules_present' and 'self.modules_running' lists
        """

        for present_module in os.listdir(MODULES_DIRECTORY):
            if os.path.isfile(f"{MODULES_DIRECTORY}/{present_module}/main.py"):
                self.modules_present.append(present_module)
            else:
                self.logger.warning(f"Malformed module '{present_module}'; missing 'main.py'")

        if not os.path.isfile(f"{CONFIGS_DIRECTORY}/modules.json"):
            raise FileNotFoundError("Missing 'modules.json'")
        with open(f"{CONFIGS_DIRECTORY}/modules.json", "r", encoding="ascii") as file:
            modules: list[str] = json.loads(file.read())

        for queued_module in modules:
            # if queued module does not exist in modules directory
            if queued_module not in self.modules_present:
                self.logger.warning(f"Module '{queued_module}' not found")
                continue
            self.modules_queued.append(queued_module)

    def _load_module_configs(self) -> None:
        """
        Loads configs
        """

        with open(f"{CONFIGS_DIRECTORY}/memberships.json", "r", encoding="ascii") as f:
            self.memberships_config: dict = json.loads(f.read())
        self.memberships_config = {int(x): int(y) for x, y in self.memberships_config.items()}

    async def load_all_queued(self) -> None:
        """
        Loads all queued modules
        """

        async def coro(module):
            module_path = f"{MODULES_DIRECTORY}.{module}.main"
            try:
                await self.client.load_extension(module_path)
            except commands.ExtensionError as e:
                self.logger.warning(f"Module '{module}' failure", exc_info=e)
                return
            self.modules_running.append(module)

        await asyncio.gather(*[coro(queued) for queued in self.modules_queued])
        self.modules_queued.clear()

    async def give_membership(self, member: discord.Member) -> None:
        """
        Grants members server membership
        """

        # check if user has the role
        role_id = self.memberships_config[member.guild.id]
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
            if guild.id not in self.memberships_config:
                self.logger.warning(f"Memberships not configured for '{guild.name}' [{guild.id}]")
                continue

            await asyncio.gather(*[coro(mem) for mem in guild.members])

    async def load_module(self, module: str) -> None:
        """
        Loads a module
        :param module: module name
        """

        if module not in self.modules_present:
            raise commands.CommandError("Module with this name doesn't exist")
        if module in self.modules_running:
            raise commands.CommandError("Module with this name is already loaded")

        module_path = make_module_path(module)
        await self.client.load_extension(module_path)

        self.modules_running.append(module)

    async def unload_module(self, module: str) -> None:
        """
        Unloads a module
        :param module: module name
        """

        if module not in self.modules_present:
            raise commands.CommandError("Module with this name doesn't exist")
        if module not in self.modules_running:
            raise commands.CommandError("Module with this name is not loaded")
        if module in self.modules_static:
            raise commands.CommandError("Static modules cannot be unloaded")

        module_path = make_module_path(module)
        await self.client.unload_extension(module_path)

        self.modules_running.remove(module)

    async def reload_module(self, module: str) -> None:
        """
        Reloads a module
        :param module: module name
        """

        if module not in self.modules_present:
            raise commands.CommandError("Module with this name doesn't exist")
        if module not in self.modules_running:
            raise commands.CommandError("Module with this name is not loaded")
        if module == self.module_name:
            raise commands.CommandError("Cannot reload self")

        module_path = make_module_path(module)
        await self.client.reload_extension(module_path)

    @app_commands.command(name="module-load", description="loads a module")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        module="name of the module")
    async def load_module_command(
            self,
            interaction: discord.Interaction,
            module: str
    ) -> None:
        """
        Loads a given module
        """

        await self.load_module(module)

        embed = discord.Embed(
            title="Success!",
            description=f"Module '{module}' is now loaded",
            color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="module-unload", description="unloads a module")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        module="name of the module")
    async def unload_module_command(
            self,
            interaction: discord.Interaction,
            module: str
    ) -> None:
        """
        Unloads a given module
        """

        await self.unload_module(module)

        embed = discord.Embed(
            title="Success!",
            description=f"Module '{module}' was unloaded",
            color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="module-reload", description="reloads a module")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        module="name of the module")
    async def reload_module_command(
        self,
        interaction: discord.Interaction,
        module: str
    ) -> None:
        """
        Reloads a given module
        """

        await self.reload_module(module)

        embed = discord.Embed(
            title="Success!",
            description=f"Module '{module}' was reloaded",
            color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="module-list", description="lists modules and their status")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_modules_command(
        self,
        interaction: discord.Interaction
    ) -> None:
        """
        Lists all modules
        """

        # 0 - present / inactive
        # 1 - active

        # modules
        # [(name, status), (name, status), (name, status), ...]
        modules_status: list[tuple[str, int]] = []
        for module in self.modules_running:
            modules_status.append((module, 1))
        for module in self.modules_present:
            # skip already appended modules
            if module in self.modules_running:
                continue
            modules_status.append((module, 0))

        modules_status.sort(key=lambda x: len(x[0]) * (x[1]+1), reverse=True)

        embed = discord.Embed(title="Module list", color=discord.Color.green())
        for status in modules_status:
            embed.add_field(
                name=status[0],
                value="✅ active" if status[1] else "❌ inactive")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(BotUtilsModule(client))
