"""
This is Tickets module that adds a ticket reporting system
"""


import asyncio
import discord
import logging
import aiosqlite
from datetime import datetime
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
        self.module_config: ModuleConfig = ModuleConfig(self.module_name)  # per module config
        self.guild_configs: GuildConfigCollection = GuildConfigCollection(self.module_name)  # per guild config

        # databases
        self.db_handle: DatabaseHandle = DatabaseHandle(self.module_name)
        self.db: aiosqlite.Connection | None = None

    async def on_cleanup(self):
        """
        Gets called when the bot is exiting
        """

        # close the database on clean up
        await self.db_handle.close()
        self.logger.info("Database closed")

    async def on_ready(self):
        """
        When the module is loaded
        """

        # connect to database
        self.db = await self.db_handle.connect()
        self.logger.info("Database connected")

        # create table for database
        async with self.db.cursor() as cur:
            cur: aiosqlite.Cursor

            await cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                TicketThreadId INTEGER PRIMARY KEY,
                TicketCreatorId INTEGER,
                TicketReportedId INTEGER,
                TicketCreationDate INTEGER,
                TicketStatus INTEGER DEFAULT 0
            );
            """)

        # commit changes
        await self.db.commit()

    @app_commands.command(name="report", description="reports user")
    @app_commands.checks.cooldown(3, 300)
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

        # ignore user reporting themselves
        if interaction.user == user:
            raise commands.UserInputError("Cannot report yourself")

        user_id = interaction.user.id
        async with self.db.cursor() as cur:
            cur: aiosqlite.Cursor

            # fetch number of tickets from user
            query = await cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM reports WHERE TicketCreatorId = ? AND TicketStatus = 0) AS TicketCount
                FROM reports
                WHERE TicketCreatorId = ?
                """, (user_id, user_id,))

            # make number
            ticket_query = await query.fetchone()
            ticket_count = ticket_query[0] if ticket_query is not None else 0

            # get max ticket number
            max_ticket_number = self.module_config.max_ticket_count

            # if max ticket number reached
            if ticket_count >= max_ticket_number:
                raise commands.CommandError("Maximum number of tickets reached")

            # get guild config
            guild_config = self.guild_configs.get(interaction.guild_id)
            if guild_config is None:
                raise commands.CommandError("Please contact your server administrator to enable `/report` feature")

            # fetch channel
            channel = interaction.guild.get_channel(guild_config.tickets_channel)
            if channel is None:
                raise commands.CommandError("Please contact your server administrator to enable `/report` feature")

            # post private thread
            thread = await channel.create_thread(
                name=f"Report on '{user.display_name}/{user.id}' for "
                     f"'{reason[:16]}{'...' if len(reason) >= 16 else ''}'",
                reason=f"Report of '{user.display_name}' by '{interaction.user.display_name}'",
                type=discord.ChannelType.private_thread)

            # create ticket data
            ticket_thread_id = thread.id
            ticket_creator_id = interaction.user.id
            ticket_reported_id = user.id
            ticket_creation_date = int(datetime.now().timestamp())

            # create ticket in database
            await cur.execute(
                "INSERT INTO reports VALUES (?, ?, ?, ?, 0)",
                (ticket_thread_id, ticket_creator_id, ticket_reported_id, ticket_creation_date,))

        # commit changes in DB
        await self.db.commit()

        # create response
        embed = discord.Embed(
            title="Success!",
            description=f"Your ticket was successfully created;\n"
                        f"You can add any additional information about the report in {thread.mention}",
            color=discord.Color.green())

        # send response
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # add reporting user
        await thread.add_user(interaction.user)

        # fetch ping roles
        ping_roles = []
        for role_id in guild_config.moderation_roles:
            if (role := interaction.guild.get_role(int(role_id))) is not None:
                ping_roles.append(role)
        ping_message = "; ".join(role.mention for role in ping_roles)

        # post message with info
        embed = discord.Embed(
            title=f"Ticket #{ticket_thread_id}",
            description=f"Ticket ID: {ticket_thread_id}\n"
                        f"Ticket Creator: {interaction.user.mention}\n"
                        f"Reported User: {user.mention}\n"
                        f"Report Reason: {reason}\n"
                        f"Ticket Creation Date: <t:{ticket_creation_date}:D>",
            color=discord.Color.orange())
        await thread.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

        # ping moderation team
        if ping_message:
            await thread.send(f"Moderation team: {ping_message}")

    @app_commands.command(name="report-close", description="closes the report")
    async def report_close_command(
            self,
            interaction: discord.Interaction
    ) -> None:
        """
        Closes the report.
        Only the user who created the report, or the administration are able to do that
        """

        # db variables
        thread_id = interaction.channel_id

        # closing reason
        reason = ""

        async with self.db.cursor() as cur:
            cur: aiosqlite.Cursor

            # fetch ticket
            query = await cur.execute("SELECT * FROM reports WHERE TicketThreadId = ?", (thread_id,))
            ticket = await query.fetchone()

            # if ticket is none -> raise wrong channel error
            if ticket is None:
                raise commands.UserInputError("Wrong channel")

            # if TicketCreatorId is not equal to id of the user calling the command
            if ticket[1] != interaction.user.id:
                # if the calling user doesn't have 'manage_threads' permissions
                if not interaction.user.guild_permissions.manage_threads:
                    raise commands.MissingPermissions(["manage_threads"])

                reason = "Closed by administrator"
            else:
                reason = "Closed by user"

            # user either has privilege or is the creator of the ticket
            await cur.execute("""
            UPDATE reports SET
                TicketStatus = 1
            WHERE TicketThreadId = ?
            """, (thread_id,))

        # lock the thread
        thread = interaction.guild.get_thread(thread_id)
        await thread.edit(locked=True, reason=reason)

        # commit db changes
        await self.db.commit()

        # create response
        embed = discord.Embed(
            title="Success!",
            description=f"Ticket #{thread_id} closed;\n"
                        f"Reason: '{reason}'",
            color=discord.Color.green())

        # send response
        await interaction.response.send_message(embed=embed)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(TicketsModule(client))
