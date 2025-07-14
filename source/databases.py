"""
Handling of databases
"""


import aiosqlite
from source.settings import *


async def connect_database(module_name: str) -> aiosqlite.Connection:
    """
    Connects and returns database
    :param module_name: name of the module
    :return: database connection
    """

    database_path = f"{VARS_DIRECTORY}/{module_name}.sqlite"
    return await aiosqlite.connect(database_path)
