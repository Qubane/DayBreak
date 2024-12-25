"""
YouTube's videos and streams fetching
"""


import asyncio
import aiohttp
from typing import Any
from datetime import datetime
from dataclasses import dataclass
from source.settings import YOUTUBE_API_KEY


@dataclass
class Thumbnail:
    """
    Class containing thumbnail data
    """

    url: str
    width: int
    height: int

    @staticmethod
    def from_response(response: dict):
        """
        Generates 'self' from API response
        """

        return Thumbnail(
            url=response["url"],
            width=response["width"],
            height=response["height"])

    @staticmethod
    def dict_from_response(thumbnails: dict[str, dict]):
        """
        Return dictionary of 'definition': Thumbnail(...)
        :param thumbnails: API response field
        :return: dict of thumbnails
        """

        return {key: Thumbnail.from_response(value) for key, value in thumbnails.items()}


@dataclass
class Video:
    """
    Class containing video information
    """

    id: str
    title: str
    description: str
    published_at: datetime
    thumbnails: dict[str, Thumbnail]
    position: int

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        return False

    @staticmethod
    def from_response(response: dict):
        """
        Generates 'self' from API response
        """

        return Video(
            id=response["resourceId"]["videoId"],
            title=response["title"],
            description=response["description"],
            published_at=datetime.fromisoformat(response["publishedAt"]),
            thumbnails=Thumbnail.dict_from_response(response["thumbnails"]),
            position=response["position"])


@dataclass
class Channel:
    """
    Class containing channel information
    """

    id: str
    title: str
    description: str
    custom_url: str
    published_at: datetime
    thumbnails: dict[str, Thumbnail]
    country: str

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.id == other.id
        return False

    @staticmethod
    def from_response(response: dict):
        """
        Generates 'self' from API response
        """

        return Channel(
            id=response["id"],
            title=response["snippet"]["title"],
            description=response["snippet"]["description"],
            custom_url=response["snippet"]["customUrl"],
            published_at=datetime.fromisoformat(response["snippet"]["publishedAt"]),
            thumbnails=Thumbnail.dict_from_response(response["snippet"]["thumbnails"]),
            country=response["snippet"]["country"])


class Fetcher:
    """
    Fetching class
    """

    # cached list of channel's upload playlist ids
    # "channel_id": "upload_id"
    channel_upload_playlists: dict[str, str] = {}

    # cached requests
    # "request_url": {"etag": "current_etag", "data": ...}
    cached: dict[str, dict[str, Any]] = dict()

    @classmethod
    def update_cache(cls, url: str, etag: str, data: Any) -> None:
        """
        Updates cache
        :param url: url request
        :param etag: API etag
        :param data: data
        """

        cls.cached[url] = {
            "etag": etag,
            "data": data}

    @classmethod
    async def fetch_api(cls, url: str, headers: dict[str, Any] | None = None):
        """
        Fetches response using given URL and HEADERS
        :param url: url request
        :param headers: headers to use
        :return: response
        """

        cached = cls.cached.get(url)

        _headers = dict()
        if cached is not None:  # cache hit
            _headers["If-None-Match"] = cached["etag"]
        if headers is not None:  # added headers
            _headers.update(headers)

        async with aiohttp.ClientSession(headers=_headers) as session:
            async with session.get(url) as resp:
                if resp.status == 304:  # cache is unchanged
                    return cached["data"]
                elif resp.status == 200:  # cache is changed / new entry
                    response = await resp.json()
                    cls.update_cache(url, response["etag"], response)
                    return response
                else:  # error
                    return None

    @classmethod
    async def fetch_channel_info(cls, channel_id: str) -> Channel:
        """
        Fetches information about a given channel.
        :param channel_id: channel id
        :return: channel information dictionary. Snippet port of API response
        """

        """
        Example response:
        {
          "kind": "youtube#channelListResponse",
          "etag": "IS9PazQv3-yvhjZ-XZTgoT-ez40",
          "pageInfo": {
            "totalResults": 1,
            "resultsPerPage": 5
          },
          "items": [
            {
              "kind": "youtube#channel",
              "etag": "1xnwFMBecF998HoKDSJ3rtCOB9o",
              "id": "UCL-8FVaefmqox59LpOJxnOQ",
              "snippet": {
                "title": "Qubik",
                "description": "...",
                "customUrl": "@qubane",
                "publishedAt": "2017-05-06T16:08:53Z",
                "thumbnails": {
                  "default": {
                    "url": "...",
                    "width": 88,
                    "height": 88
                  },
                  "medium": {
                    "url": "...",
                    "width": 240,
                    "height": 240
                  },
                  "high": {
                    "url": "...",
                    "width": 800,
                    "height": 800
                  }
                },
                "localized": {
                  "title": "Qubik",
                  "description": "..."
                },
                "country": "RU"
              }
            }
          ]
        }
        """

        response = await cls.fetch_api(
            f"https://www.googleapis.com/youtube/v3/channels?"
            f"part=snippet&"
            f"id={channel_id}&"
            f"key={YOUTUBE_API_KEY}")

        return Channel.from_response(response["items"][0])

    @classmethod
    async def fetch_channel_playlist_id(cls, channel_id: str) -> str:
        """
        Fetches channel playlist id
        :param channel_id: channel id
        :return: id of channels playlist
        """

        """
        Example response:
        {
          "kind": "youtube#channelListResponse",
          "etag": "-MN_iD2qDxM2j7txDFiyj2v_9mo",
          "pageInfo": {
            "totalResults": 1,
            "resultsPerPage": 5
          },
          "items": [
            {
              "kind": "youtube#channel",
              "etag": "m0GtIUQJozlbjUCz4ucQW6SYClw",
              "id": "UCL-8FVaefmqox59LpOJxnOQ",
              "contentDetails": {
                "relatedPlaylists": {
                  "likes": "",
                  "uploads": "UUL-8FVaefmqox59LpOJxnOQ"
                }
              }
            }
          ]
        }
        """

        if channel_id not in cls.channel_upload_playlists:
            content_details = await cls.fetch_api(
                f"https://www.googleapis.com/youtube/v3/channels?"
                f"part=contentDetails&"
                f"id={channel_id}&"
                f"key={YOUTUBE_API_KEY}")
            uploads_id = content_details["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            cls.channel_upload_playlists[channel_id] = uploads_id  # cache result
        else:
            uploads_id = cls.channel_upload_playlists[channel_id]

        return uploads_id

    @classmethod
    async def fetch_videos(cls, channel_id: str, amount: int) -> list[Video]:
        """
        Returns a list of videos on the channel.
        :param channel_id: channel id
        :param amount: amount of videos to fetch
        :return: list of video ids. items part of API response
        """

        """
        Example response:
        [
          {
            "kind": "youtube#playlistItem",
            "etag": "us4-o9nIFLi8LyeSvFAEnj_jdh8",
            "id": "VVVMLThGVmFlZm1xb3g1OUxwT0p4bk9RLktPdWZzdndxdC1N",
            "snippet": {
              "publishedAt": "2024-08-26T12:00:31Z",
              "channelId": "UCL-8FVaefmqox59LpOJxnOQ",
              "title": "...",
              "description": "...",
              "thumbnails": {
                "default": {
                  "url": "https://i.ytimg.com/vi/KOufsvwqt-M/default.jpg",
                  "width": 120,
                  "height": 90
                },
                "medium": {...},
                "high": {...},
                "standard": {...},
                "maxres": {...}
              },
              "channelTitle": "Qubik",
              "playlistId": "UUL-8FVaefmqox59LpOJxnOQ",
              "position": 0,
              "resourceId": {
                "kind": "youtube#video",
                "videoId": "KOufsvwqt-M"
              },
              "videoOwnerChannelTitle": "Qubik",
              "videoOwnerChannelId": "UCL-8FVaefmqox59LpOJxnOQ"
            },
            "contentDetails": {
              "videoId": "KOufsvwqt-M",
              "videoPublishedAt": "2024-08-26T12:00:31Z"
            }
          }
        ]
        """

        # fetch last {amount} videos
        uploads_id = await cls.fetch_channel_playlist_id(channel_id)
        playlist = await cls.fetch_api(
            f"https://www.googleapis.com/youtube/v3/playlistItems?"
            f"part=snippet%2CcontentDetails&"
            f"maxResults={amount}&"
            f"playlistId={uploads_id}&"
            f"key={YOUTUBE_API_KEY}")

        return [Video.from_response(x["snippet"]) for x in playlist["items"]]


async def test():
    """
    Very cool test thingy. runs only when file is run as main
    """

    for _ in range(3):
        response = await Fetcher.fetch_videos(r"UCL-8FVaefmqox59LpOJxnOQ", 3)
        # response = await Fetcher.fetch_channel_info(r"UCL-8FVaefmqox59LpOJxnOQ")
        # response = json.dumps(response, indent=2)
        print('\n'.join([str(x) for x in response]))

    # channels = [
    #     "UCL-8FVaefmqox59LpOJxnOQ",
    #     "UCXuqSBlHAE6Xw-yeJA0Tunw",
    #     "UCiER8p540j2SosO7OX7E0VA",
    # ]
    #
    # responses = await asyncio.gather(*[Fetcher.fetch_videos(x, 2) for x in channels])
    # print(responses)


if __name__ == '__main__':
    asyncio.run(test())
