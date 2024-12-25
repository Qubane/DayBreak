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


class BotUtilsModule(commands.Cog):
    """
    Bot utils module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # modules
        self.modules_present: list[str] = list()
        self.modules_queued: list[str] = list()
        self.modules_running: list[str] = list()

        # important modules
        self.modules_queued.append("BotUtils")
        self.modules_queued.append("ExceptionHandler")

        # "guild_id": "role_id"
        self.memberships_config: dict[int, int] | None = None

        # config and module loading
        self._load_configs()
        self._load_modules()

    def _load_modules(self) -> None:
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

    def _load_configs(self) -> None:
        """
        Loads configs
        """

        with open(f"{CONFIGS_DIRECTORY}/memberships.json", "r", encoding="ascii") as f:
            self.memberships_config: dict = json.loads(f.read())
        self.memberships_config = {int(x): int(y) for x, y in self.memberships_config.items()}

    @app_commands.command(name="reload", description="reloads a module")
    @app_commands.describe(
        module="name of the module")
    async def example(
        self,
        interaction: discord.Interaction,
        module: str
    ) -> None:
        """
        This is an example slash command
        """


async def setup(client: commands.Bot) -> None:
    await client.add_cog(BotUtilsModule(client))
