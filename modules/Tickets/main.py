"""
This is Tickets module that adds a ticket reporting system
"""


import asyncio
import discord
import logging
import discord.ui
from datetime import datetime, timezone
from discord import app_commands, Interaction
from discord.ext import commands
from source.configs import *
from source.databases import *


class ReportModal(discord.ui.Modal, title="Report information"):
    description = discord.ui.TextInput(
        label="Report description",
        style=discord.TextStyle.long,
        placeholder="Short description of your problem...",
        required=True)

    def __init__(self, cog: "TicketsModule"):
        super().__init__()

        self.cog = cog

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.send_message("Your ticket will appear shortly", ephemeral=True)
        await self.cog.create_ticket(interaction, self.description.value)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        self.cog.logger.warning("Error occurred during modal submission", exc_info=error)


class ReportButton(discord.ui.View):
    def __init__(self, cog: "TicketsModule"):
        super().__init__(timeout=None)

        self.cog = cog

    @discord.ui.button(
        label="Create ticket",
        style=discord.ButtonStyle.blurple,
        custom_id="persistent_button:report_button")
    async def report_button(self, interaction: discord.Interaction, button: discord.Button):
        await interaction.response.send_modal(ReportModal(self.cog))


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

    async def on_cleanup(self):
        """
        Gets called when the bot is exiting
        """

    async def on_ready(self):
        """
        When the module is loaded
        """

        self.client.add_view(ReportButton(self))

    @commands.command("ticket-test")
    @commands.is_owner()
    async def command_make_announce(
            self,
            ctx: commands.Context
    ) -> None:
        """
        Temporary command for creating a ticket button
        """

        await ctx.message.delete()
        await ctx.send(view=ReportButton(self))

    async def create_ticket(self, interaction: discord.Interaction, description: str):
        """
        Creates a ticket from interaction
        """

        # fetch guild config
        guild_config = self.guild_configs.get(interaction.guild_id)
        if guild_config is None:
            return

        # fetch channel
        channel = interaction.guild.get_channel(guild_config.tickets_channel)

        # post private thread
        thread = await channel.create_thread(
            name=f"Report from {interaction.user.display_name}",
            type=discord.ChannelType.private_thread)

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
            title=f"Ticket made by {interaction.user.display_name}",
            description=f"Ticket ID: {thread.id}\n"
                        f"Ticket Creator: {interaction.user.mention}\n"
                        f"Report Reason: {description[:512]}\n"
                        f"Ticket Creation Date: <t:{datetime.now(tz=timezone.utc).timestamp():.0f}:D>",
            color=discord.Color.orange())
        await thread.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

        # ping moderation team
        if ping_message:
            await thread.send(f"Report reviewed by: {ping_message}")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(TicketsModule(client))
