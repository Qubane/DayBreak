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


class MathUtilsModule(commands.Cog):
    """
    Math Utils module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

    @staticmethod
    def render_latex_formula(formula: str) -> BytesIO:
        """
        Renders formatted LaTeX formula
        :param formula: LaTeX formula
        :return: bytesio image
        """

        img = BytesIO()
        sympy.preview(
            f"$${formula}$$",
            output="png",
            viewer="BytesIO",
            outputbuffer=img,
            euler=False,
            dvioptions=['-D', '400'])
        pil_image = ImageOps.expand(Image.open(img), border=20, fill='white')
        img.seek(0)
        pil_image.save(img, "PNG")
        img.seek(0)

        return img

    @app_commands.command(name="latex", description="converts LaTeX formula to image")
    @app_commands.describe(text="LaTeX formatted formula")
    async def render_latex_formula_cmd(
            self,
            interaction: discord.Interaction,
            text: str
    ) -> None:
        """
        Command that adds LaTeX rendering
        """

        try:
            img = self.render_latex_formula(text)
        except RuntimeError as exc:
            error = exc.__str__()
            error = error[error.find("! ")+2:]
            error = error[:error.find("\\r")]
            await interaction.response.send_message(error, ephemeral=True)
        else:
            await interaction.response.send_message(file=discord.File(img, filename="result.png"))

    @app_commands.command(name="solve", description="solves equation")
    @app_commands.describe(
        equation="an equation",
        unknowns="list of unknown variables [for multiple use ';', 'x;y;z']")
    async def solve_latex_equation(
            self,
            interaction: discord.Interaction,
            equation: str,
            unknowns: str = ''
    ) -> None:
        """
        Solves a given equation
        """

        if unknowns:
            symbols = [sympy.Symbol(x) for x in unknowns.split(";")]
        else:
            symbols = None

        try:
            eq: sympy.Expr = sympy.parsing.sympy_parser.parse_expr(equation, evaluate=False)
        except sympy.parsing.sympy_parser.TokenError as e:
            raise app_commands.AppCommandError(e.__str__())

        try:
            solutions = sympy.solvers.solvers.solve(eq, symbols=symbols)
        except Exception as e:
            raise app_commands.AppCommandError(e.__str__())

        msg = f"```\nYou entered:\n{sympy.pretty(eq)}\n\nSolutions:\n"
        for solution in solutions:
            if isinstance(solution, dict):
                sol = list(solution.items())
                msg += f"{sol[0]} = {sol[1]}"
            elif isinstance(solution, sympy.Expr):
                msg += sympy.pretty(solution)
            else:
                msg += str(solution)
            msg += "\n"
        msg += "```"

        await interaction.response.send_message(msg)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(MathUtilsModule(client))
