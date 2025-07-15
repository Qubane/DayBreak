"""
Handling loading of configurations for modules
"""


import os
import json
from source.utils import DotDict
from source.settings import CONFIGS_MODULES_DIRECTORY, CONFIGS_GUILDS_DIRECTORY


class ModuleConfig:
    """
    Container for per-module configuration
    """

    def __init__(self, module_name: str):
        self.module_name = module_name.lower()
        self.config_path: str = f"{CONFIGS_MODULES_DIRECTORY}/{self.module_name}.json"

        # load raw config
        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config: DotDict = DotDict(json.load(file))

    def __getattr__(self, item):
        if item in self._config:
            return getattr(self._config, item)
        else:
            raise AttributeError


class GuildConfig:
    """
    Container for per-guild module configuration.
    Not intended to be used by itself. Instead, used as part of GuildConfigCollection
    """

    def __init__(self, guild_id: str | int, module_name: str):
        self.config_path: str = f"{CONFIGS_GUILDS_DIRECTORY}/{guild_id}/{module_name}.json"

        # load raw config
        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config: DotDict = DotDict(json.load(file))

    def __getattr__(self, item):
        if item in self._config:
            return getattr(self._config, item)
        else:
            raise AttributeError


class GuildConfigCollection:
    """
    Collection of per-guild configs
    """

    def __init__(self, module_name: str):
        self.module_name: str = module_name.lower()
        self._guild_configs: dict[str, GuildConfig] = {}

        # load in configs
        for guild_id in os.listdir(CONFIGS_GUILDS_DIRECTORY):
            try:
                # add config
                self._guild_configs[str(guild_id)] = GuildConfig(guild_id, self.module_name)
            except OSError:
                # if file wasn't found, or any kind of other OS related error
                pass

    def __setitem__(self, key, value):
        if isinstance(value, GuildConfig):
            self._guild_configs[str(key)] = value
        else:
            raise TypeError

    def __getitem__(self, item):
        return self._guild_configs[str(item)]

    def __contains__(self, item):
        return self._guild_configs.__contains__(str(item))

    def __iter__(self):
        return self._guild_configs.values().__iter__()

    def get(self, item, default=None) -> GuildConfig | None:
        return self._guild_configs.get(str(item), default)
