"""
Handling loading of configurations for modules
"""


import os
import json
from types import NoneType
from collections import namedtuple
from source.settings import CONFIGS_MODULES_DIRECTORY, CONFIGS_GUILDS_DIRECTORY


def _create_attributes(config: dict) -> list[tuple]:
    """
    Converts a config dictionary into a list of recursive attributes
    :param config: configuration dictionary
    :return: attribute list
    """

    attr_list = []
    for key, value in config.items():
        # end value
        if isinstance(value, (str, int, list, NoneType)):
            # append to list of attributes
            attr_list.append((key, value))

        # sub config
        elif isinstance(value, dict):
            # get attribute list
            recur_attr_list: list = _create_attributes(value)

            # get names for attributes
            attr_names = []
            attr_values = []
            for attr in recur_attr_list:
                # named tuple
                if hasattr(attr, "_fields"):
                    # append name and named tuple itself
                    attr_names.append(attr.__class__.__name__)
                    attr_values.append(attr)

                # normal tuple
                else:
                    # append name and value
                    attr_names.append(attr[0])
                    attr_values.append(attr[1])

            # make multi-value attribute
            attr_tuple = namedtuple(key, attr_names)

            # append to list of attributes
            attr_list.append(attr_tuple(*attr_values))
        else:
            raise NotImplementedError

    # return list of attributes
    return attr_list


def _set_object_attributes(obj: object, config: dict):
    """
    Sets the attributes of an object
    :param obj: object
    :param config: configs
    """

    for attribute in _create_attributes(config):
        if hasattr(attribute, "_fields"):
            setattr(obj, attribute.__class__.__name__, attribute)
        else:
            setattr(obj, attribute[0], attribute[1])


class ModuleConfig:
    """
    Container for per-module configuration
    """

    def __init__(self, module_name: str):
        self.module_name = module_name.lower()
        self.config_path: str = f"{CONFIGS_MODULES_DIRECTORY}/{self.module_name}.json"

        # load raw config
        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config: dict = json.load(file)

        # set self attributes
        _set_object_attributes(self, self._config)


class GuildConfig:
    """
    Container for per-guild module configuration.
    Not intended to be used by itself. Instead, used as part of GuildConfigCollection
    """

    def __init__(self, guild_id: str | int, module_name: str):
        self.config_path: str = f"{CONFIGS_GUILDS_DIRECTORY}/{guild_id}/{module_name}.json"

        # load raw config
        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config: dict = json.load(file)

        # set self attributes
        _set_object_attributes(self, self._config)


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

    def get(self, item) -> GuildConfig | None:
        return self._guild_configs.get(str(item))
