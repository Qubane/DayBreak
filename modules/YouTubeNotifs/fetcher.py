"""
YouTube's videos and streams fetching
"""

import requests
from source.settings import YOUTUBE_API_KEY


class Fetcher:
    """
    Fetching class
    """

    # cached list of channel's upload playlist ids
    # "channel_id": "upload_id"
    channel_upload_playlists: dict[str, str] = {}

    @classmethod
    def fetch_videos(cls, channel_id: str, amount: int) -> dict[str, str | dict]:
        """
        Returns a list of videos on the channel.
        :param channel_id: channel id
        :param amount: amount of videos to fetch
        :return: list of video ids
        """

        """
        Example return:
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
            content_details = requests.get(
                f"https://www.googleapis.com/youtube/v3/channels?"
                f"part=contentDetails&"
                f"id={channel_id}&"
                f"key={YOUTUBE_API_KEY}",
                headers={"Accept-Encoding": "gzip,deflate"}).json()
            uploads_id = content_details["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            cls.channel_upload_playlists[channel_id] = uploads_id
        else:
            uploads_id = cls.channel_upload_playlists[channel_id]

        # fetch last {amount} videos
        playlist = requests.get(
            f"https://www.googleapis.com/youtube/v3/playlistItems?"
            f"part=snippet%2CcontentDetails&"
            f"maxResults={amount}&"
            f"playlistId={uploads_id}&"
            f"key={YOUTUBE_API_KEY}",
            headers={"Accept-Encoding": "gzip,deflate"}).json()

        return playlist["items"]


def test():
    print(Fetcher.fetch_videos(r"UCL-8FVaefmqox59LpOJxnOQ", 10))


if __name__ == '__main__':
    test()
