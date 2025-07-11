"""
This is Sentiments module for DayBreak.
It adds sentiment / positivity leaderboard.
Depending on how positive the messages are sent by user, they will be placed higher or lower on the leaderboard
It uses AI model to perform sentiment analysis on message, and update the leaderboard accordingly.
"""


import os
import math
import json
import asyncio
import discord
import logging
from typing import Callable
import transformers.pipelines
from discord import app_commands
from transformers import pipeline
from contextlib import contextmanager
from discord.ext import commands, tasks
from source.configs import *


def cast_result_to_numeric(label: str) -> int:
    """
    Casts string label to numeric
    :param label: result label
    :return: int 1 - 5
    """

    match label:
        case "Very Positive":
            return 5
        case "Positive":
            return 4
        case "Neutral":
            return 3
        case "Negative":
            return 2
        case "Very Negative":
            return 1
        case _:
            raise ValueError(f"Unknown label '{label}'")


def magic_number_formula(positivity_score: float, message_count: int) -> float:
    """
    Does the magic to calculate the magic number
    :param positivity_score: database value of user
    :param message_count: database value of user
    :return: magic number
    """

    return (positivity_score / message_count) + math.log(message_count, 10)


class SentimentsModule(commands.Cog):
    """
    Sentiments module
    """

    def __init__(self, client: commands.Bot) -> None:
        self.client = client

        # logging
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.logger.info("Module loaded")

        # model
        self.pipeline: transformers.pipelines.Pipeline = pipeline(
            "text-classification",
            model="tabularisai/multilingual-sentiment-analysis",
            truncation=True)

        # path to Sentiments database
        self.db_path = "var/sentiments_leaderboard.json"
        if not os.path.isfile(self.db_path):  # create file if missing
            with open(self.db_path, "w", encoding="utf-8") as f:
                f.write("{}")

        # configs
        self.module_config: ModuleConfig = ModuleConfig("Sentiments")

        # processing queue
        self.message_processing_queue: list[discord.Message] = []

        # start task
        self.process_queued.change_interval(seconds=self.module_config.queue_process_interval)
        self.process_queued.start()

    @contextmanager
    def use_database(self, guild_id: str | int | None = None):
        """
        User database context manager
        """

        # the bot is small enough for json "databases" to be ok
        with open(self.db_path, "r", encoding="utf-8") as file:
            database: dict[str, dict] = json.load(file)

        # if guild id parameter is present the guild is not yet present -> add it
        if guild_id is not None and str(guild_id) not in database:
            database[str(guild_id)] = dict()

        # manage context
        try:
            # yield whole database if no guild is provided
            if guild_id is None:
                yield database

            # yield guild's database
            else:
                yield database[str(guild_id)]
        finally:
            # store new database
            with open(self.db_path, "w", encoding="utf-8") as file:
                json.dump(database, file)

    @staticmethod
    def update_user(user: int | str, database: dict[str, dict], **kwargs) -> None:
        """
        Update user from database
        :param user: user id
        :param database: database context
        :param kwargs: keyword arguments. Uses lambdas to affect the user parameters, for 'set' use 'lambda x: const'
        """

        # make sure id is a string
        user = str(user)

        # if user is not present
        if user not in database:
            database[user] = dict()

        # write data to user
        for key, func in kwargs.items():
            func: Callable
            database[user][key] = func(database[user].get(key, 0))

    def get_guild_leaderboard(self, guild_id: int | str) -> list[tuple[int, float]]:
        """
        Returns guild's leaderboard
        :param guild_id: guild id
        :return: leaderboard
        """

        # fetch and process guild's database
        leaderboard: list[tuple[int, float]] = []
        with self.use_database(guild_id) as database:
            for user_id, user_dict in database.items():
                # calculate user
                magic_number = magic_number_formula(user_dict["p_val"], user_dict["msg_n"])
                leaderboard.append((user_id, magic_number))

        # sort users
        leaderboard.sort(key=lambda x: x[1], reverse=True)

        # return leaderboard
        return leaderboard

    @tasks.loop(minutes=5)
    async def process_queued(self) -> None:
        """
        Perform sentiment analysis on queued messages
        """

        # skip if there's nothing to process
        if len(self.message_processing_queue) == 0:
            return

        # compile content together
        messages: list[str] = [""]
        reference: list[discord.Message] = [self.message_processing_queue[0]]
        for queued_message in self.message_processing_queue:
            is_dif_author = queued_message.author.id != reference[-1].author.id
            is_dif_guild = queued_message.guild.id != reference[-1].guild.id

            # if the message's author or guild are not the same as they were before
            if is_dif_author or is_dif_guild:
                # append new author to messages
                messages.append(queued_message.content + "\n")
                reference.append(queued_message)
            else:
                # if the context is too long
                if len(messages[-1]) >= 256:
                    messages.append("")
                    reference.append(queued_message)

                # append content
                messages[-1] += queued_message.content + "\n"

        # clear queue
        self.message_processing_queue.clear()

        # process messages
        results = [cast_result_to_numeric(x["label"]) / 5 for x in self.pipeline(messages)]

        # update database
        with self.use_database() as database:
            # update database according to where the message was sent
            for ref, result in zip(reference, results):
                # make sure guild database is present
                if str(ref.guild.id) not in database:
                    database[str(ref.guild.id)] = dict()

                # update user
                self.update_user(
                    ref.author.id, database[str(ref.guild.id)],
                    msg_n=lambda x: x + 1,  # add 1 to message number
                    p_val=lambda x: x + result  # add result to p value (positivity value)
                )

    @app_commands.command(name="posiboard", description="positivity leaderboard")
    async def posiboard(
            self,
            interaction: discord.Interaction
    ) -> None:
        """
        Implementation for positivity leaderboard
        """

        # get leaderboard
        leaderboard = self.get_guild_leaderboard(interaction.guild_id)

        # filter users who left
        leaderboard = list(filter(lambda x: (interaction.guild.get_member(int(x[0])) is not None), leaderboard))

        # make embed
        embed = discord.Embed(title="Positivity leaderboard", color=discord.Color.green())

        # add fields. Top 5 users
        for user in leaderboard[:5]:
            embed.add_field(
                name=interaction.guild.get_member(int(user[0])).display_name,
                value=f"Positivity score is {user[1] * 100:.0f}",
                inline=False)

        # display the embed
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="posiself", description="Positivity of self")
    async def posiself(
            self,
            interaction: discord.Interaction
    ) -> None:
        """
        Implementation for positivity of self
        """

        # get leaderboard
        leaderboard = self.get_guild_leaderboard(interaction.guild_id)

        # index user
        for idx, (user_id, magic_number) in enumerate(leaderboard, start=1):
            if str(user_id) == str(interaction.user.id):
                break

        # if the loop finished (didn't break before that), means the user was not found
        else:
            # create response
            embed = discord.Embed(
                title="error 404: We don't know you yet!",
                description="You are new to this server, so write more stuff to see the posiself!",
                color=discord.Color.brand_green())

            # send response
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # early return
            return

        # number postfix
        # Outputs `10st` (tenst), `20nd` (twentynd), `30rd` (thirtyrd)
        #
        # "it's not a bug, it's *character*" - @arminius97 (discord)
        #
        if str(idx)[0] == "1":
            postfix = "st"
        elif str(idx)[0] == "2":
            postfix = "nd"
        elif str(idx)[0] == "3":
            postfix = "rd"
        else:
            postfix = "th"

        # make embed
        embed = discord.Embed(title=f"Posiself of {interaction.user.display_name}", color=discord.Color.green())
        embed.set_author(name=interaction.user.display_name)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(
            name=f"Positivity score",
            value=f"{magic_number * 100:.0f} magic number{'s' if magic_number > 1 else ''}!", inline=False)
        embed.add_field(name=f"Place on the posiboard", value=f"You are in the {idx}{postfix} place!", inline=False)
        embed.set_footer(text="don't take this score at face value, it's just a magic number")

        # send response
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Append message for processing
        """

        # skip bot messages
        if message.author.bot:
            return

        # skip messages in DM's
        if isinstance(message.channel, discord.DMChannel):
            return

        # add message to queue
        self.message_processing_queue.append(message)

        # check if queue size exceeds the configured size
        if len(self.message_processing_queue) > self.module_config.queue_max_size:
            # create task to process queued
            asyncio.create_task(self.process_queued)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SentimentsModule(client))
