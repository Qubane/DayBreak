"""
YouTube's videos and streams fetching
"""

import json
import asyncio
import aiohttp
from source.settings import YOUTUBE_API_KEY


class Fetcher:
    """
    Fetching class
    """

    # cached list of channel's upload playlist ids
    # "channel_id": "upload_id"
    channel_upload_playlists: dict[str, str] = {}

    @staticmethod
    async def fetch_channel_info(channel_id: str):
        """
        Fetches information about a given channel.
        :param channel_id: channel id
        :return: channel information dictionary. Direct API response
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

        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://www.googleapis.com/youtube/v3/channels?"
                    f"part=snippet&"
                    f"id={channel_id}&"
                    f"key={YOUTUBE_API_KEY}",
                    headers={"Accept-Encoding": "gzip,deflate"}) as resp:
                response = await resp.json()

        return response["items"][0]["snippet"]

    @classmethod
    async def fetch_videos(cls, channel_id: str, amount: int) -> dict[str, str | dict]:
        """
        Returns a list of videos on the channel.
        :param channel_id: channel id
        :param amount: amount of videos to fetch
        :return: list of video ids. items part of API response
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

        # fetch upload list id
        if channel_id not in cls.channel_upload_playlists:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"https://www.googleapis.com/youtube/v3/channels?"
                        f"part=contentDetails&"
                        f"id={channel_id}&"
                        f"key={YOUTUBE_API_KEY}",
                        headers={"Accept-Encoding": "gzip,deflate"}) as resp:
                    content_details = await resp.json()
            uploads_id = content_details["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            cls.channel_upload_playlists[channel_id] = uploads_id
        else:
            uploads_id = cls.channel_upload_playlists[channel_id]

        # fetch last {amount} videos
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://www.googleapis.com/youtube/v3/playlistItems?"
                    f"part=snippet%2CcontentDetails&"
                    f"maxResults={amount}&"
                    f"playlistId={uploads_id}&"
                    f"key={YOUTUBE_API_KEY}",
                    headers={"Accept-Encoding": "gzip,deflate"}) as resp:
                playlist = await resp.json()

        return playlist["items"]


async def test():
    """
    Very cool test thingy. runs only when file is run as main
    """

    # response = await Fetcher.fetch_videos(r"UCL-8FVaefmqox59LpOJxnOQ", 10)
    # response = await Fetcher.fetch_channel_info(r"UCL-8FVaefmqox59LpOJxnOQ")
    # response = json.dumps(response, indent=2)
    # print(response)

    channels = [
        "UCL-8FVaefmqox59LpOJxnOQ",
        "UCXuqSBlHAE6Xw-yeJA0Tunw",
        "UCiER8p540j2SosO7OX7E0VA",
    ]

    responses = await asyncio.gather(*[Fetcher.fetch_videos(x, 2) for x in channels])
    print(responses)


if __name__ == '__main__':
    asyncio.run(test())
