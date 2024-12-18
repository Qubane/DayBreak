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
    async def fetch_channel_info(channel_id: str) -> dict[str, str | dict]:
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
    async def fetch_videos(cls, channel_id: str, amount: int) -> list[dict[str, str | dict]]:
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
                "medium": {
                  "url": "https://i.ytimg.com/vi/KOufsvwqt-M/mqdefault.jpg",
                  "width": 320,
                  "height": 180
                },
                "high": {
                  "url": "https://i.ytimg.com/vi/KOufsvwqt-M/hqdefault.jpg",
                  "width": 480,
                  "height": 360
                },
                "standard": {
                  "url": "https://i.ytimg.com/vi/KOufsvwqt-M/sddefault.jpg",
                  "width": 640,
                  "height": 480
                },
                "maxres": {
                  "url": "https://i.ytimg.com/vi/KOufsvwqt-M/maxresdefault.jpg",
                  "width": 1280,
                  "height": 720
                }
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
          },
          {
            "kind": "youtube#playlistItem",
            "etag": "4mscx-jC4FjxhbnBz1b4fU4C4Ss",
            "id": "VVVMLThGVmFlZm1xb3g1OUxwT0p4bk9RLi01VGFKWG9HNHBv",
            "snippet": {
              "publishedAt": "2024-07-28T15:45:22Z",
              "channelId": "UCL-8FVaefmqox59LpOJxnOQ",
              "title": "...",
              "description": "...",
              "thumbnails": {
                "default": {
                  "url": "https://i.ytimg.com/vi/-5TaJXoG4po/default.jpg",
                  "width": 120,
                  "height": 90
                },
                "medium": {
                  "url": "https://i.ytimg.com/vi/-5TaJXoG4po/mqdefault.jpg",
                  "width": 320,
                  "height": 180
                },
                "high": {
                  "url": "https://i.ytimg.com/vi/-5TaJXoG4po/hqdefault.jpg",
                  "width": 480,
                  "height": 360
                },
                "standard": {
                  "url": "https://i.ytimg.com/vi/-5TaJXoG4po/sddefault.jpg",
                  "width": 640,
                  "height": 480
                },
                "maxres": {
                  "url": "https://i.ytimg.com/vi/-5TaJXoG4po/maxresdefault.jpg",
                  "width": 1280,
                  "height": 720
                }
              },
              "channelTitle": "Qubik",
              "playlistId": "UUL-8FVaefmqox59LpOJxnOQ",
              "position": 1,
              "resourceId": {
                "kind": "youtube#video",
                "videoId": "-5TaJXoG4po"
              },
              "videoOwnerChannelTitle": "Qubik",
              "videoOwnerChannelId": "UCL-8FVaefmqox59LpOJxnOQ"
            },
            "contentDetails": {
              "videoId": "-5TaJXoG4po",
              "videoPublishedAt": "2024-07-28T15:45:22Z"
            }
          },
          {
            "kind": "youtube#playlistItem",
            "etag": "mfx697vD6gDvlnMU5MRiwwP7utk",
            "id": "VVVMLThGVmFlZm1xb3g1OUxwT0p4bk9RLkZyUEVKcVdxU3JN",
            "snippet": {
              "publishedAt": "2024-07-26T11:00:13Z",
              "channelId": "UCL-8FVaefmqox59LpOJxnOQ",
              "title": "...",
              "description": "...",
              "thumbnails": {
                "default": {
                  "url": "https://i.ytimg.com/vi/FrPEJqWqSrM/default.jpg",
                  "width": 120,
                  "height": 90
                },
                "medium": {
                  "url": "https://i.ytimg.com/vi/FrPEJqWqSrM/mqdefault.jpg",
                  "width": 320,
                  "height": 180
                },
                "high": {
                  "url": "https://i.ytimg.com/vi/FrPEJqWqSrM/hqdefault.jpg",
                  "width": 480,
                  "height": 360
                },
                "standard": {
                  "url": "https://i.ytimg.com/vi/FrPEJqWqSrM/sddefault.jpg",
                  "width": 640,
                  "height": 480
                },
                "maxres": {
                  "url": "https://i.ytimg.com/vi/FrPEJqWqSrM/maxresdefault.jpg",
                  "width": 1280,
                  "height": 720
                }
              },
              "channelTitle": "Qubik",
              "playlistId": "UUL-8FVaefmqox59LpOJxnOQ",
              "position": 2,
              "resourceId": {
                "kind": "youtube#video",
                "videoId": "FrPEJqWqSrM"
              },
              "videoOwnerChannelTitle": "Qubik",
              "videoOwnerChannelId": "UCL-8FVaefmqox59LpOJxnOQ"
            },
            "contentDetails": {
              "videoId": "FrPEJqWqSrM",
              "videoPublishedAt": "2024-07-26T11:00:13Z"
            }
          }
        ]
        """

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

    response = await Fetcher.fetch_videos(r"UCL-8FVaefmqox59LpOJxnOQ", 3)
    # response = await Fetcher.fetch_channel_info(r"UCL-8FVaefmqox59LpOJxnOQ")
    response = json.dumps(response, indent=2)
    print(response)

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
