"""
Twitch stream fetching
"""


import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def check_live(channel_name: str) -> bool:
    """
    Return twitch channel status
    :param channel_name: name of the twitch channel
    :return: True when streamer is live
    """

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.twitch.tv/{channel_name}") as resp:
            return True if 'isLiveBroadcast' in (await resp.text("utf-8")) else False


async def get_title(channel_name: str) -> str:
    """
    Returns stream's title
    :param channel_name: name of the twitch channel
    :return: stream title
    """

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.twitch.tv/{channel_name}") as resp:
            soup = BeautifulSoup(await resp.read(), features="html.parser")
    return soup.find("meta", property="og:description")["content"]


async def test():
    print(await get_title("mutzbunny"))


if __name__ == '__main__':
    asyncio.run(test())
