"""
Handling of databases
"""


import aiosqlite
from source.settings import *


async def insert_or_ignore_user(cur: aiosqlite.Cursor, table_name: str, user_id: int | str) -> None:
    """
    SQL query
    'INSERT OR IGNORE INTO {table_name} (UserId) VALUES ({user_id});'
    :param cur: database cursor
    :param table_name: guild table name
    :param user_id: user id
    """

    await cur.execute(f"INSERT OR IGNORE INTO {table_name} (UserId) VALUES (?)", (user_id,))


async def create_table_if_not_exists(cur: aiosqlite.Cursor, guild_ids: list[int | str], query: str) -> None:
    """
    SQL query
    'CREATE TABLE IF NOT EXISTS {table_name} (...)'
    :param cur: database cursor
    :param guild_ids: list of guild id's
    :param query: table creation query ({table_name} for table name)
    """

    # iterate through guilds and append them
    for guild_id in guild_ids:
        table_name = f"g{guild_id}"

        await cur.execute(query.format(table_name=table_name))


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
