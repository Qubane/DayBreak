"""
Generic settings for the bot
"""


import os
import logging
import logging.handlers


# root paths
MODULES_DIRECTORY = "modules"   # cogs source code
CONFIGS_DIRECTORY = "configs"   # bot configurations
VARS_DIRECTORY = "var"          # modules storage
LOGS_DIRECTORY = "logs"         # bot logs

# sub paths
KEYS_DIRECTORY = f"{CONFIGS_DIRECTORY}/keys"                # references to keys used by modules
CONFIGS_MODULES_DIRECTORY = f"{CONFIGS_DIRECTORY}/modules"  # global module configs
CONFIGS_GUILDS_DIRECTORY = f"{CONFIGS_DIRECTORY}/guilds"    # per-guild module configs


def init():
    # create 'var' directory
    # 'var' directory is used for storing data for modules
    if not os.path.isdir(VARS_DIRECTORY):
        os.makedirs(VARS_DIRECTORY)

    # create 'keys' directory
    # 'keys' directory is used for references to keynames for the KeyChain class
    if not os.path.isdir(KEYS_DIRECTORY):
        os.makedirs(KEYS_DIRECTORY)

    # create 'modules' directory
    # 'modules' directory is used by modules for storing their global configuration
    if not os.path.isdir(CONFIGS_MODULES_DIRECTORY):
        os.makedirs(CONFIGS_MODULES_DIRECTORY)

    # create 'guilds' directory
    # 'guilds' directory is used by modules for storing per-guild configuration
    if not os.path.isdir(CONFIGS_GUILDS_DIRECTORY):
        os.makedirs(CONFIGS_GUILDS_DIRECTORY)

    # create 'logs' directory
    if not os.path.isdir(LOGS_DIRECTORY):
        os.makedirs(LOGS_DIRECTORY)

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
