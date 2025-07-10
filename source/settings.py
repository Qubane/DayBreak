"""
Generic settings for the bot
"""


import os
import logging
import logging.handlers


# paths
MODULES_DIRECTORY = "modules"
CONFIGS_DIRECTORY = "configs"
VARS_DIRECTORY = "var"
LOGS_DIRECTORY = "logs"
KEYS_DIRECTORY = "keys"


def init():
    # create 'var' directory
    # 'var' directory is used for storing data for modules
    if not os.path.isdir(VARS_DIRECTORY):
        os.mkdir(VARS_DIRECTORY)

    # create 'keys' directory
    # 'keys' directory is used for references to keynames for the KeyChain class
    if not os.path.isdir(KEYS_DIRECTORY):
        os.mkdir(KEYS_DIRECTORY)

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
