"""
Handling loading of configurations for modules
"""


import json
from collections import namedtuple
from source.settings import CONFIGS_MODULES_DIRECTORY, CONFIGS_GUILDS_DIRECTORY


def create_attributes(config: dict) -> list[tuple]:
    """
    Converts a config dictionary into a list of recursive attributes
    :param config: configuration dictionary
    :return: attribute list
    """

    attr_list = []
    for key, value in config.items():
        # end value
        if isinstance(value, (str, int, list)):
            # make attribute
            attr_tuple = namedtuple(key, str(key))

            # append to list of attributes
            attr_list.append(attr_tuple(value))

        # sub config
        elif isinstance(value, dict):
            # get attribute list
            recur_attr_list: list = create_attributes(value)

            # get names for attributes
            attr_names = [x.__class__.__name__ for x in recur_attr_list]

            # make multi-value attribute
            attr_tuple = namedtuple(key, attr_names)

            # append to list of attributes
            attr_list.append(attr_tuple(*recur_attr_list))
        else:
            raise NotImplementedError

    # return list of attributes
    return attr_list


class ModuleConfig:
    """
    Container for per-module configuration
    """

    def __init__(self, module_name: str):
        self.config_path: str = f"{CONFIGS_MODULES_DIRECTORY}/{module_name}"

        # load raw config
        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config: dict = json.load(file)


class GuildConfig:
    """
    Container for per-guild module configuration
    """

    def __init__(self, guild_id: str | int):
        self.config_path: str = f"{CONFIGS_GUILDS_DIRECTORY}/{guild_id}"

        # load raw config
        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config: dict = json.load(file)

        # TODO: attribute conversion
