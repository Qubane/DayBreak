"""
Main DayBreak bot entry file.
This is what you run to start the bot
"""


import asyncio
import discord
import logging
import source.settings
from discord.ext import commands
from source.keychain import KeyChain
from source.settings import MODULES_DIRECTORY


class Client(commands.Bot):
    """
    Main bot client
    """

    def __init__(self):
        super(Client, self).__init__(command_prefix="!", intents=discord.Intents.all(),
                                     help_command=None)

        # logger
        self.logger: logging.Logger = logging.getLogger(__name__)

    async def close(self) -> None:
        """
        Call cleanups for cogs (if present)
        """

        # clean up tasks
        cleanup_tasks = [cog.on_cleanup() for cog in self.cogs.values() if hasattr(cog, "on_cleanup")]
        await asyncio.gather(*cleanup_tasks)

        # actually close the bot
        await super().close()

    async def setup_hook(self) -> None:
        """
        Module loading after the client's successful login
        """

        # load static module
        await self.load_extension(f"{MODULES_DIRECTORY}.Core.main")


def main():
    """
    Main entrance to the bot
    """

    # Useless message at the start of the bot
    if __import__("os").name != "nt":
        print("NOTE: You are running on non-windows machine, some of the things may be buggy\n"
              "Please report any issues to 'https://github.com/Qubane/DayBreak/issues'\n\n")

    client = Client()
    client.run(KeyChain.DISCORD_API_KEY, root_logger=True, log_handler=None)


if __name__ == '__main__':
    source.settings.init()
    main()
