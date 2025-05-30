"""
Manages API keys
"""


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
            cls._update_keychain()

        # return the API key.
        # raise an error if the key cannot be fetched
        return cls._mapping[name]

    @classmethod
    def _update_keychain(cls):
        """
        Updates KeyChain class
        """
