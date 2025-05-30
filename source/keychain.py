"""
Manages API keys
"""


import os
import logging
from typing import TextIO
from source.settings import CONFIGS_DIRECTORY


LOGGER: logging.Logger = logging.getLogger(__name__)


class KeyChain:
    """
    Manages API Keys
    """

    # keychain mapping
    _mapping: dict[str, str]

    @classmethod
    def key(cls, name: str) -> str:
        """
        Returns API key.
        :param name: API key name
        :return: API key string
        :raises: KeyError when key is not found
        """

        # if name is missing, try to update the keychain
        if name not in cls._mapping:
            cls.update_keychain()

        # return the API key.
        # raise an error if the key cannot be fetched
        return cls._mapping[name]

    @classmethod
    def update_keychain(cls):
        """
        Updates KeyChain class
        """

        # go through files
        for file in os.listdir(CONFIGS_DIRECTORY):
            # skip all non-keys files
            if os.path.splitext(file)[1] != ".keys":
                continue

            # make filepath
            filepath = f"{CONFIGS_DIRECTORY}/{file}"

            # get keys
            with open(filepath, "r", encoding="utf-8") as f:
                keys = cls._return_file_keys(f)

            # try making mapping
            for key in keys:
                # fetch environment variable
                env = os.getenv(key)

                # if it's none -> log an error
                if env is None:
                    LOGGER.error(f"Error when fetching the API environment variable: {key}")
                    continue

                # map the environment variable
                cls._mapping[key] = env

    @staticmethod
    def _return_file_keys(file: TextIO) -> list[str]:
        """
        Returns keys from file
        :param file: file handle
        :return: list of string keys
        """

        # read keys
        keys = []
        for key in file.readlines():
            keys.append(key.strip())  # append stripped key

        # return keys
        return keys


# update KeyChain
KeyChain.update_keychain()
