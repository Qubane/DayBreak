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
            # append to list of attributes
            attr_list.append((key, value))

        # sub config
        elif isinstance(value, dict):
            # get attribute list
            recur_attr_list: list = create_attributes(value)

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


def set_object_attributes(obj: object, config: dict):
    """
    Sets the attributes of an object
    :param obj: object
    :param config: configs
    """

    for attribute in create_attributes(config):
        if hasattr(attribute, "_fields"):
            setattr(obj, attribute.__class__.__name__, attribute)
        else:
            setattr(obj, attribute[0], attribute[1])


class ModuleConfig:
    """
    Container for per-module configuration
    """

    def __init__(self, module_name: str):
        # self.config_path: str = f"{CONFIGS_MODULES_DIRECTORY}/{module_name}"
        self.config_path = module_name

        # load raw config
        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config: dict = json.load(file)

        # set self attributes
        set_object_attributes(self, self._config)


class GuildConfig:
    """
    Container for per-guild module configuration
    """

    def __init__(self, guild_id: str | int):
        self.config_path: str = f"{CONFIGS_GUILDS_DIRECTORY}/{guild_id}"

        # load raw config
        with open(self.config_path, "r", encoding="utf-8") as file:
            self._config: dict = json.load(file)

        # set self attributes
        set_object_attributes(self, self._config)
