"""
This is Tickets module that adds a ticket reporting system
"""


import discord
import logging
import aiosqlite
from discord import app_commands
from discord.ext import commands, tasks
from source.configs import *
from source.databases import *


class TicketsModule(commands.Cog):
    """
    Tickets module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client: commands.Bot = client
        self.module_name: str = "Tickets"

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # configs
        # self.module_config: ModuleConfig = ModuleConfig(self.module_name)  # per module config
        # self.guild_configs: GuildConfigCollection = GuildConfigCollection(self.module_name)  # per guild config

        # databases
        self.db_handle: DatabaseHandle = DatabaseHandle(self.module_name)
        self.db: aiosqlite.Connection | None = None

    async def on_cleanup(self):
        """
        Gets called when the bot is exiting
        """

        # close the database on clean up
        await self.db_handle.close()

    async def on_ready(self):
        """
        When the module is loaded
        """

        # connect to database
        self.db = await self.db_handle.connect()

        # create table for database
        async with self.db.cursor() as cur:
            cur: aiosqlite.Cursor

            await cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                TicketThreadId INTEGER PRIMARY KEY,
                TicketCreatorId INTEGER,
                TicketReportedId INTEGER,
                TicketCreationDate INTEGER
            );
            """)

        # commit changes
        await self.db.commit()

    @app_commands.command(name="report", description="reports user")
    @app_commands.describe(
        reason="reason for the report",
        user="user that will be reported")
    async def report_command(
        self,
        interaction: discord.Interaction,
        reason: str,
        user: discord.Member
    ) -> None:
        """
        Creates a report ticket
        """


async def setup(client: commands.Bot) -> None:
    await client.add_cog(TicketsModule(client))
