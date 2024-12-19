"""
Main DayBreak bot file.
This is what you run to start the bot
"""


import os
import json
import asyncio
import discord
import logging
import source.settings
from source.settings import MODULES_DIRECTORY, CONFIGS_DIRECTORY
from discord.ext import commands


class Client(commands.Bot):
    """
    Main bot client
    """

    def __init__(self):
        super(Client, self).__init__(command_prefix="!", intents=discord.Intents.all(),
                                     help_command=None)

        self.logger: logging.Logger = logging.getLogger(__name__)

        self.modules_present: list[str] = list()
        self.modules_queued: list[str] = list()
        self.modules_running: list[str] = list()

        # "guild_id": "role_id"
        self.memberships_config: dict[int, int] | None = None

        self._load_configs()
        self._load_modules()

    def _load_modules(self) -> None:
        """
        Loads 'self.modules_present' and 'self.modules_running' lists
        """

        for present_module in os.listdir(MODULES_DIRECTORY):
            # check for complete module
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

    async def setup_hook(self) -> None:
        """
        Module loading after the client's successful login
        """

        for queued_module in self.modules_queued:
            try:
                await self.load_extension(f"{MODULES_DIRECTORY}.{queued_module}.main")
            except commands.ExtensionError as e:
                self.logger.warning(f"Module '{queued_module}' failure", exc_info=e)
                continue
            self.modules_running.append(queued_module)
        self.modules_queued.clear()

    async def on_ready(self) -> None:
        """
        Things that happen after bot connects to gateway
        """

        self.logger.info("Bot connected.")
        await self.change_presence(activity=discord.Game("A DayBreak"))
        await self.tree.sync()
        self.logger.info("Command tree synced")

        # membership test
        for guild in self.guilds:
            # skip guild if membership is not configured
            if guild.id not in self.memberships_config:
                self.logger.warning(f"Memberships not configured for '{guild.name}' [{guild.id}]")
                continue
            for member in guild.members:
                await self.add_membership(member)

    async def on_member_join(self, member: discord.Member) -> None:
        """
        When a new user joins
        """

        await self.add_membership(member)

    async def add_membership(self, member: discord.Member) -> None:
        """
        Adds membership to user
        :param member: discord guild member
        """

        # check if guild is configured
        if member.guild.id not in self.memberships_config:
            return

        # check if user has the role
        role_id = self.memberships_config[member.guild.id]
        if role_id in member._roles:
            return

        # add role, if missing
        await member.add_roles(member.guild.get_role(role_id))


def main():
    """
    Main entrance to the bot
    """

    # Useless message at the start of the bot
    if os.name != "nt":
        print("NOTE: You are running on non-windows machine, some of the things may be buggy\n"
              "Please report any issues to 'https://github.com/UltraQbik/daybreak/issues'\n\n")

    client = Client()
    client.run(source.settings.DISCORD_API_KEY, root_logger=True, log_handler=None)


if __name__ == '__main__':
    source.settings.init()
    main()
