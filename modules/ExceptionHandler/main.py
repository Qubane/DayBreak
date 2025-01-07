"""
This is a module that adds global exception handling
Always imported, and cannot be unloaded, only reloaded
"""


import discord
import logging
from discord import app_commands
from discord.ext import commands


class ExceptionHandlerModule(commands.Cog):
    """
    Exception handling module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # add global exception handler
        self.client.tree.error(coro=self.on_command_error)

    @commands.Cog.listener()
    async def on_command_error(
            self,
            interaction: commands.Context | discord.Interaction,
            error: commands.ExtensionError):
        """
        Global exception handler
        """

        embed = discord.Embed(color=discord.Color.red())
        if isinstance(error, (app_commands.MissingPermissions, commands.MissingPermissions)):
            embed.title = error.__class__.__name__
            embed.description = "List of missing permissions"
            for permission in error.missing_permissions:
                embed.add_field(name="Missing permission:", value=permission, inline=False)
        elif isinstance(error, (app_commands.CommandInvokeError, commands.CommandInvokeError)):
            raise error
        elif isinstance(error, (app_commands.AppCommandError, commands.CommandError)):
            embed.title = error.__class__.__name__
            embed.description = error.args[0]
        else:
            self.logger.warning("An error had occurred while handling another error", exc_info=error)
            embed.title = "Unexpected error!"
            embed.description = "Unhandled exception had occurred, please contact @qubane"

        if isinstance(interaction, discord.Interaction):
            if interaction.response.type is discord.InteractionResponseType.deferred_channel_message:
                await interaction.followup.send(embed=embed)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.send(embed=embed, reference=interaction.message)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ExceptionHandlerModule(client))
