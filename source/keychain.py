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

                # set the attribute
                setattr(cls, key, env)

        # log info
        LOGGER.info("KeyChain updated")

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
