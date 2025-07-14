"""
Core bot module.
Adds the ability to load, unload and reload other modules
Always imported, and cannot be unloaded, only reloaded
"""


import os
import asyncio
import discord
import logging
from discord import app_commands
from discord.ext import commands
from source.configs import *
from source.settings import MODULES_DIRECTORY


def make_module_path(module: str) -> str:
    """
    Makes proper paths for modules, so they could be worked with
    :param module: module name
    :return: module path
    """

    return f"{MODULES_DIRECTORY}.{module}.main"


class CoreModule(commands.Cog):
    """
    Core module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client: commands.Bot = client
        self.module_name: str = "Core"

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

        # config and module loading
        self.load_config()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        When the bot successfully connects to discord's websocket
        """

        self.logger.info("Bot connected")

        await self.load_all_queued()
        self.logger.info("All modules loaded")

        await self.client.change_presence(activity=discord.Game("A DayBreak"))

    def load_config(self) -> None:
        """
        Loads 'self.modules_present' and 'self.modules_running' lists
        """

        # create all present modules
        self.modules_present.clear()
        for present_module in os.listdir(MODULES_DIRECTORY):
            # if the module is correctly setup
            if os.path.isfile(f"{MODULES_DIRECTORY}/{present_module}/main.py"):
                self.modules_present.append(present_module)

            # if module is missing 'main.py' file
            else:
                self.logger.warning(f"Malformed module '{present_module}'; missing 'main.py'")

        # load configs
        config = ModuleConfig("modules")

        # load active modules into queue
        for queued_module in config.active_modules:
            # if queued module does not exist in modules directory
            if queued_module not in self.modules_present:
                self.logger.warning(f"Module '{queued_module}' not found")
                continue

            # append module to queue
            self.modules_queued.append(queued_module)

    async def load_all_queued(self) -> None:
        """
        Loads all queued modules
        """

        async def coro(module):
            # try to load the module
            try:
                # load module
                await self.client.load_extension(make_module_path(module))

                # append to running modules
                self.modules_running.append(module)

            # in case of exception
            except commands.ExtensionError as e:
                self.logger.warning(f"Module '{module}' failure", exc_info=e)

        # gather queued modules and load them
        await asyncio.gather(*[coro(queued) for queued in self.modules_queued])

        # clear queued modules
        self.modules_queued.clear()

    async def load_module(self, module: str) -> None:
        """
        Loads a module
        :param module: module name
        """

        # load module
        module_path = make_module_path(module)
        await self.client.load_extension(module_path)

        # append to running modules
        self.modules_running.append(module)

    async def unload_module(self, module: str) -> None:
        """
        Unloads a module
        :param module: module name
        """

        # unload module
        module_path = make_module_path(module)
        await self.client.cogs[module_path].on_cleanup()
        await self.client.unload_extension(module_path)

        # remove from running modules
        self.modules_running.remove(module)

    async def reload_module(self, module: str) -> None:
        """
        Reloads a module
        :param module: module name
        """

        # reload module
        module_path = make_module_path(module)
        await self.client.cogs[module_path].on_cleanup()
        await self.client.reload_extension(module_path)

    async def reload_self(self) -> None:
        """
        Reloads entire bot
        """

        self.logger.info("Reloading self")

        # unload all running modules (except Core)
        await asyncio.gather(
            *[self.unload_module(module) for module in self.modules_running if module != self.module_name])

        # load configs
        self.load_config()

        # add static modules to queued
        self.modules_queued += self.modules_static

        # remove core from queued
        self.modules_queued.remove(self.module_name)

        # load all queued modules
        await self.load_all_queued()

        self.logger.info("Reload complete")

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

        if module not in self.modules_present:
            raise commands.CommandError("Module with this name doesn't exist")
        if module in self.modules_running:
            raise commands.CommandError("Module with this name is already loaded")

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

        if module not in self.modules_present:
            raise commands.CommandError("Module with this name doesn't exist")
        if module not in self.modules_running:
            raise commands.CommandError("Module with this name is not loaded")
        if module in self.modules_static:
            raise commands.CommandError("Static modules cannot be unloaded")

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

        if module not in self.modules_present:
            raise commands.CommandError("Module with this name doesn't exist")
        if module not in self.modules_running:
            raise commands.CommandError("Module with this name is not loaded")

        if module == self.module_name:  # reload bot
            await self.reload_self()
        else:
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

        # modules
        # [(name, status), (name, status), (name, status), ...]
        modules_status: list[tuple[str, str]] = list()
        self.modules_running.sort(key=lambda x: len(x))
        self.modules_present.sort(key=lambda x: len(x))
        for module in self.modules_running:
            modules_status.append((f"{module}{' [STATIC]' if module in self.modules_static else ''}", "✅ active"))
        for module in self.modules_present:
            # skip already appended modules
            if module in self.modules_running:
                continue
            modules_status.append((f"{module}", "❌ inactive"))

        embed = discord.Embed(title="Module list", color=discord.Color.green())
        for status in modules_status:
            embed.add_field(name=status[0], value=status[1], inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="bot-upgrade", description="upgrade bot")
    async def upgrade_bot_command(
        self,
        interaction: discord.Interaction
    ) -> None:
        """
        Upgrades bot. Can only be used by owner of the bot
        """

        if not (await self.client.is_owner(interaction.user)):
            raise commands.MissingPermissions(
                ["bot_owner"], "You must be a host of this bot to run this command")

        self.logger.info("initiated bot upgrade")

        # import subprocess
        import subprocess

        # run "git pull" (unpythonic :< )
        self.logger.info("running 'git pull'...")
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)

        # skip if up to date
        if "Already up to date." in result.stdout:
            self.logger.info("Already up to date, no harm done")
        else:
            self.logger.info("Updates found")

            # reload self
            self.logger.info("Calling 'self' to reload...")
            await self.reload_self()

        # create embed
        self.logger.info(f"Bot upgrade finished with message:\n{result.stdout}")
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Success",
                description=f"Message: \n{result.stderr}\n{result.stdout}",
                color=discord.Color.green()),
            ephemeral=True)

    @app_commands.command(name="bot-sync", description="sync command tree")
    async def sync_bot_command(
            self,
            interaction: discord.Interaction
    ) -> None:
        """
        Syncs up the command tree.
        """

        if not (await self.client.is_owner(interaction.user)):
            raise commands.MissingPermissions(
                ["bot_owner"], "You must be a host of this bot to run this command")

        await self.client.tree.sync()
        self.logger.info("Command tree synced")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(CoreModule(client))
