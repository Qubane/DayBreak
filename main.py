import os
import sys
import json
import discord
from discord.ext import commands


class Client(commands.Bot):
    """
    Main bot client
    """

    def __init__(self):
        super(Client, self).__init__(command_prefix="!", intents=discord.Intents.all(),
                                     help_command=None)


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
