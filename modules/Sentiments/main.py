"""
This is Sentiments module for DayBreak.
It adds sentiment / positivity leaderboard.
Depending on how positive the messages are sent by user, they will be placed higher or lower on the leaderboard
It uses AI model to perform sentiment analysis on message, and update the leaderboard accordingly.
"""


import discord
import logging
import transformers.pipelines
from discord import app_commands
from transformers import pipeline
from discord.ext import commands, tasks


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

        # processing queue
        self.message_processing_queue: list[discord.Message] = []

        # start task
        self.process_queued.start()

    def update_database_user(self, user: int, **kwargs) -> None:
        """
        Updates users data
        :param user: user id
        :param kwargs: key arguments
        """

    @tasks.loop(seconds=30)
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
        results = self.pipeline(messages)

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
