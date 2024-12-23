"""
This is an example module for DayBreak bot
"""


import discord
import logging
from discord import app_commands
from discord.ext import commands


class ExceptionHandlerModule(commands.Cog):
    """
    This is an example module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # add global exception handler
        self.client.tree.error(coro=self.on_command_error)

    @commands.Cog.listener()
    async def on_command_error(self, interaction: discord.Interaction, error: commands.ExtensionError):
        """
        Global exception handler
        """

        embed = discord.Embed(color=discord.Color.red())
        if isinstance(error, app_commands.MissingPermissions):      # missing permissions
            embed.title = error.__class__.__name__
            embed.description = "List of missing permissions"
            for permission in error.missing_permissions:
                embed.add_field(name="Missing permission:", value=permission, inline=False)
        else:                                                       # unhandled exception
            self.logger.warning("An error had occurred while handling another error", exc_info=error)
            embed.title = "Unexpected error!"
            embed.description = "Unhandled exception had occurred, please contact @qubane"
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ExceptionHandlerModule(client))
