"""
This is the module, that adds miscellaneous commands and features to the bot.
These commands are not integral parts of the bot, and can be ignored for the most part.

Code is taken from 'Qubane/MightyOmegaBot' repo path 'client_cogs/RoflCommands/main.py'
"""


import discord
import logging
from discord.ext import commands
from discord import app_commands


class MiscModule(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

    @app_commands.command(name="bk", description="boykisser")
    async def boy_kisser(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"{interaction.user.mention} You like kissing boys don't you?")

    @app_commands.command(name="morning-tea", description="recipe for nice morning tea")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def morning_tea(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"# Morning tea recipe:\n"
            f"- dirty mug - 1 thing\n"
            f"- the spoon - 1 thing\n"
            f"- pepper - all of it\n"
            f"- tea bags / powder / leafs - 6 (or all for better effect)\n"
            f"- hot water - quarter of the mug\n"
            f"- milk - half of the mug (or 3/4 s if you're using hydraulic press to push the tea bags into the mug)\n"
            f"# Making it:\n"
            f"1. Put the mug on any flat and horizontal surface.\n"
            f"2. Gently throw all the tea bags. If some of them fall on the floor, do following sub steps\n"
            f"  1. Pick them up\n"
            f"  2. Spit on them\n"
            f"  3. Rub them on your pants, to get rid of any dirt, and dry them off\n"
            f"2. Passionately shove them into the mug\n"
            f"3. Push them further into the mug using the spoon, use hydraulic press if needed\n"
            f"4. Pour hot water into the mug\n"
            f"5. If you've used all tea bags, then shake the tea powder from the box the tea was in\n"
            f"6. Fill the rest of the mug with milk\n"
            f"7. Mix the tea with spoon\n"
            f"8. Add pepper to the tea\n"
            f"  1. Shake the pepper, moaning in the process\n"
            f"## And voila, your tea is ready for consumption! :tea: :heart:\n")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(MiscModule(client))
