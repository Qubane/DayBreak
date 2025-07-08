"""
This is Sentiments module for DayBreak.
It adds sentiment / positivity leaderboard.
Depending on how positive the messages are sent by user, they will be placed higher or lower on the leaderboard
It uses AI model to perform sentiment analysis on message, and update the leaderboard accordingly.
"""

import os
import json
import discord
import logging
from typing import Callable
import transformers.pipelines
from discord import app_commands
from transformers import pipeline
from contextlib import contextmanager
from discord.ext import commands, tasks


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
            truncation=True,
            device="cuda")

        # here's an example path to the database
        self.db_path = "var/sentiments_leaderboard.json"
        if not os.path.isfile(self.db_path):  # create file if missing
            with open(self.db_path, "w", encoding="utf-8") as f:
                f.write("{}")

        # processing queue
        self.message_processing_queue: list[discord.Message] = []

        # start task
        self.process_queued.start()

    @contextmanager
    def use_database(self):
        """
        User database context manager
        """

        # the bot is small enough for json "databases" to be ok
        with open(self.db_path, "r", encoding="utf-8") as file:
            database: dict[str, dict] = json.load(file)

        # manage context
        try:
            yield database
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
            database[user][key] = func(database[user].get(key, 0.0))

    @tasks.loop(minutes=5)
    async def process_queued(self) -> None:
        """
        Perform sentiment analysis on queued messages
        """

        # skip if there's nothing to process
        if len(self.message_processing_queue) == 0:
            return

        # compile content together
        author_id = self.message_processing_queue[0].author.id
        author_message = ""
        messages = []
        authors = []
        for message in self.message_processing_queue:
            # if the author of the next message is the same
            if author_id == message.author.id:
                author_message += message.content + "\n"

            # if someone else wrote the next message
            else:
                # append message to messages
                messages.append(author_message)

                # append the author to authors
                authors.append(author_id)

                # update the author
                author_message = ""
                author_id = message.author.id

        # append left over message and author
        if author_message:
            messages.append(author_message)
            authors.append(author_id)

        # clear queue
        self.message_processing_queue.clear()

        # process messages
        results = [cast_result_to_numeric(x["label"]) for x in self.pipeline(messages)]

        # update database
        with self.use_database() as database:
            for author_id, result in zip(authors, results):
                self.update_user(
                    author_id, database,
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

        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Append message for processing
        """

        self.message_processing_queue.append(message)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(SentimentsModule(client))
