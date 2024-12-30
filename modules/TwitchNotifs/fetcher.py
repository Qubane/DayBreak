"""
Twitch stream fetching
"""


import json
import asyncio
import aiohttp
from typing import Any
from dataclasses import dataclass
from source.settings import TWITCH_API_ID, TWITCH_API_KEY


@dataclass(frozen=True)
class Stream:
    pass


class Fetcher:
    """
    Main twitch fetcher class
    """

    _access_token: str | None = None
    _token_type: str | None = None

    @classmethod
    async def _init_access_token(cls) -> None:
        """
        Fetches twitch API access token
        """

        async with aiohttp.ClientSession(headers={"Content-Type": "application/x-www-form-urlencoded"}) as session:
            async with session.post(
                    f"https://id.twitch.tv/oauth2/token?"
                    f"client_id={TWITCH_API_ID}&"
                    f"client_secret={TWITCH_API_KEY}&"
                    f"grant_type=client_credentials") as resp:
                response = await resp.json()
        if resp.status != 200:
            raise Exception(resp.reason)

        cls._access_token = response["access_token"]
        cls._token_type = response["token_type"].capitalize()

    @classmethod
    async def fetch_api(cls, url: str, headers: dict[str, Any] | None = None) -> dict:
        """
        Fetch API response from url
        :param url: api request link
        :param headers: additional headers
        :return: response
        """

        if cls._access_token is None:
            await cls._init_access_token()

        _headers = {
            "Authorization": f"{cls._token_type} {cls._access_token}",
            "Client-Id": TWITCH_API_ID}
        if headers is not None:
            _headers.update(headers)

        async with aiohttp.ClientSession(headers=_headers) as session:
            async with session.get(url) as resp:
                return await resp.json()

    @classmethod
    async def fetch_stream_info(cls, user_login: str) -> Stream | None:
        """
        Fetches stream info
        :param user_login: user login name
        :return: Stream dataclass if is live
        """


async def test():
    response = await Fetcher.fetch_api("https://api.twitch.tv/helix/streams?user_login=lvndmark")
    print(json.dumps(response, indent=2))


if __name__ == '__main__':
    asyncio.run(test())
