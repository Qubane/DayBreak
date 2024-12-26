"""
Generic settings for the bot
"""


import os
import logging
import logging.handlers


# keys
DISCORD_API_KEY = os.getenv("DISCORD_API_KEY")  # bot auth token
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # YouTube Data API key

# paths
MODULES_DIRECTORY = "modules"
CONFIGS_DIRECTORY = "configs"
VARS_DIRECTORY = "var"
LOGS_DIRECTORY = "logs"


def init():
    # create 'var' directory
    # 'var' directory is used for storing data for modules
    if not os.path.isdir(VARS_DIRECTORY):
        os.mkdir(VARS_DIRECTORY)

    # create 'logs' directory
    if not os.path.isdir(LOGS_DIRECTORY):
        os.mkdir(LOGS_DIRECTORY)

    # setup logging
    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{",
        format="[{asctime}] [{levelname:<8}] {name}: {message}",
        handlers=[
            logging.handlers.RotatingFileHandler(
                filename=f"{LOGS_DIRECTORY}/discord.log",
                encoding="utf-8",
                maxBytes=2**20 * 32,  # 32 MiB
                backupCount=5),
            logging.StreamHandler()])
