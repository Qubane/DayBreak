"""
Module that adds different math related utilities.
For example, it adds LaTeX formula rendering
"""


import sympy
import discord
import logging
from io import BytesIO
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

    @app_commands.command(name="latex", description="converts LaTeX formula to image")
    @app_commands.describe(text="LaTeX formatted formula")
    async def render_latex_formula(self, interaction: discord.Interaction, text: str):
        """
        Command that adds LaTeX rendering
        """

        img = BytesIO()
        try:
            sympy.preview(
                f"$${text}$$",
                output="png",
                viewer="BytesIO",
                outputbuffer=img,
                euler=False,
                dvioptions=['-D', '400'])
        except RuntimeError as exc:
            error = exc.__str__()
            error = error[error.find("! ")+2:]
            error = error[:error.find("\\r")]
            await interaction.response.send_message(error, ephemeral=True)
        else:
            pil_image = ImageOps.expand(Image.open(img), border=20, fill='white')
            img.seek(0)
            pil_image.save(img, "PNG")
            img.seek(0)
            await interaction.response.send_message(file=discord.File(img, filename="result.png"))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(MathUtilsModule(client))
