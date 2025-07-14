"""
Handling of databases
"""


import aiosqlite
from source.settings import *


class DatabaseHandle:
    """
    Database handling class
    """

    def __init__(self, module_name: str):
        self.database_path: str = f"{VARS_DIRECTORY}/{module_name.lower()}.sqlite"

        self.db: aiosqlite.Connection | None = None

    async def connect(self) -> aiosqlite.Connection:
        """
        Connects database
        :return: database connection
        """

        # if database wasn't connected
        if self.db is None:
            self.db = await aiosqlite.connect(self.database_path)

        # return connection
        return self.db

    async def close(self) -> None:
        """
        Closes database connection
        """

        # if database is connected
        if self.db is not None:
            await self.db.commit()
            await self.db.close()
