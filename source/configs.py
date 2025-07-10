"""
Handling loading of configurations for modules
"""


import json
from collections import namedtuple
from source.settings import CONFIGS_MODULES_DIRECTORY, CONFIGS_GUILDS_DIRECTORY


class ModuleConfig:
    """
    Container for per-module configuration
    """

    def __init__(self, module_name: str):
        self.config_path: str = f"{CONFIGS_MODULES_DIRECTORY}/{module_name}"

        # load raw config
        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config = json.load(file)

        # TODO: attribute conversion


class GuildConfig:
    """
    Container for per-guild module configuration
    """

    def __init__(self, guild_id: str | int):
        self.config_path: str = f"{CONFIGS_GUILDS_DIRECTORY}/{guild_id}"

        # load raw config
        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config = json.load(file)

        # TODO: attribute conversion
