import os
import sys
import json
import discord
import logging
from discord.ext import commands


MODULES_DIRECTORY = "modules"
CONFIGS_DIRECTORY = "configs"


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

        self._load_modules()

    def _load_modules(self):
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

    async def setup_hook(self) -> None:
        """
        Module loading after the client's successful connection
        """

        for queued_module in self.modules_queued:
            try:
                await self.load_extension(f"{MODULES_DIRECTORY}.{queued_module}.main")
            except commands.ExtensionError as e:
                self.logger.warning(f"Module '{queued_module}' failure", exc_info=e)
                continue
            self.modules_running.append(queued_module)
            self.modules_queued.remove(queued_module)


def main():
    """
    Main entrance to the bot
    """

    # Useless message at the start of the bot
    if os.name != "nt":
        print("NOTE: You are running on non-windows machine, some of the things may be buggy\n"
              "Please report any issues to 'https://github.com/UltraQbik/daybreak/issues'\n\n")

    client = Client()
    client.run(sys.argv[1])


if __name__ == '__main__':
    main()
