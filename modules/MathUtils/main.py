"""
Module that adds different math related utilities.
For example, it adds LaTeX formula rendering
"""


import sympy
import discord
import logging
from PIL import Image, ImageOps
from discord import app_commands
from discord.ext import commands
from source.settings import VARS_DIRECTORY


class MathUtilsModule(commands.Cog):
    """
    Math Utils module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        self.image_path: str = f"{VARS_DIRECTORY}/image.png"

    @app_commands.command(name="latex", description="converts LaTeX formula to image")
    @app_commands.describe(text="LaTeX formatted formula")
    async def render_latex_formula(self, interaction: discord.Interaction, text: str):
        """
        Command that adds LaTeX rendering
        """

        try:
            sympy.preview(
                f"$${text}$$",
                output="png",
                viewer="file",
                filename="image.png",
                euler=False,
                dvioptions=['-D', '400'])
        except RuntimeError as exc:
            text = str(exc).replace('\\n', '\n')
            out = text[text.find('! '):]
            out = out[:out.find('\n')]
            await interaction.response.send_message(out, ephemeral=True)
        else:
            with Image.open("image.png") as img:
                img_borders = ImageOps.expand(img, border=20, fill='white')
                img_borders.save("image.png")
            with open(self.image_path, "rb") as image:
                await interaction.response.send_message(file=discord.File(image))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(MathUtilsModule(client))
