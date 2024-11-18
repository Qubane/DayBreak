"""
Generic settings for the bot
"""


import os
import logging
import logging.handlers


# keys
DISCORD_API_KEY = os.getenv("DISCORD_API_KEY")  # bot auth token
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # YouTube Data API key


def init():
    # setup logging
    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
        format="[{asctime}] [{levelname:<8}] {name}: {message}",
        handlers=[
            logging.handlers.RotatingFileHandler(
                filename="logs/discord.log",
                encoding="utf-8",
                maxBytes=2**20 * 32,  # 32 MiB
                backupCount=5),
            logging.StreamHandler()]
    )


    # create 'var' directory
    # 'var' directory is used for storing data for modules
    if not os.path.isdir("var"):
        os.mkdir("var")
