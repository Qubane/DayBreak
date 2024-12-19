"""
This module adds simple utils commands.
Commands such as: latency; reload_cog; etc
"""


import discord
from discord import app_commands
from discord.ext import commands


class UtilsModule(commands.Cog):
    """
    This is an example module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

    @app_commands.command(name="latency", description="shows bots latency")
    async def latency(
        self,
        interaction: discord.Interaction
    ) -> None:
        """
        This is a simple command, that shows bot latency
        """

        embed = discord.Embed(
            title="Latency",
            description=f"Bots latency is {self.client.latency * 1000:.4f} ms",
            color=discord.Color.brand_green())

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(UtilsModule(client))
