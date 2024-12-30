"""
Twitch stream fetching
"""


import json
import asyncio
import aiohttp
from typing import Any
from datetime import datetime
from dataclasses import dataclass
from source.settings import TWITCH_API_ID, TWITCH_API_KEY


@dataclass(frozen=True)
class Stream:
    """
    Dataclass containing information about the stream
    """

    id: str
    user_id: str
    user_login: str
    user_name: str
    game_id: str
    game_name: str
    type: str
    title: str
    viewer_count: int
    started_at: datetime
    language: str
    thumbnail_url: str
    tags: list[str]
    is_mature: bool

    @staticmethod
    def from_response(response: dict):
        """
        Generates self from twitch API response
        :param response: API response
        :return: self
        """

        return Stream(
            id=response["id"],
            user_id=response["user_id"],
            user_login=response["user_login"],
            user_name=response["user_name"],
            game_id=response["game_id"],
            game_name=response["game_name"],
            type=response["type"],
            title=response["title"],
            viewer_count=response["viewer_count"],
            started_at=response["started_at"],
            language=response["language"],
            thumbnail_url=response["thumbnail_url"],
            tags=response["tags"],
            is_mature=response["is_mature"])

    def thumbnail(self, width: int, height: int) -> str:
        """
        Returns formatted URL string to stream thumbnail
        :param width: thumbnail width
        :param height: thumbnail height
        :return: thumbnail URL link
        """

        return self.thumbnail_url.format(width=width, height=height)


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

        response = await cls.fetch_api(f"https://api.twitch.tv/helix/streams?user_login={user_login}")
        if len(response["data"]) > 0:
            return Stream.from_response(response["data"][0])
        return None


async def test():
    response = await Fetcher.fetch_stream_info("mutzbunny")
    print(response)


if __name__ == '__main__':
    asyncio.run(test())
