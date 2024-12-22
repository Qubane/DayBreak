"""
Twitch stream fetching
"""


import asyncio
import aiohttp


async def check_live(channel_name: str) -> bool:
    """
    Return twitch channel status
    :param channel_name: name of the twitch channel
    :return: True when streamer is live
    """

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://www.twitch.tv/{channel_name}") as resp:
            return True if 'isLiveBroadcast' in (await resp.text("utf-8")) else False


async def test():
    print(await check_live("pewdiepie"))
    print(await check_live("CodeMaker_4"))


if __name__ == '__main__':
    asyncio.run(test())
