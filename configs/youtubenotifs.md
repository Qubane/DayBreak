# `youtubenotifs.json` file configuration
- Config file contains configurations for `YouTubeNotifs` module
- The config is subdivided into 2 categories
  - `config` - global module configuration
  - `guild_config` - guild configurations
- Global module configuration has fields
  - `update_interval` - how often the update check is performed
  - `fetching_window` - how many videos will be fetched at once
    (bigger window allows for more posted videos to be detected within the update interval)
  - `checking_window_offset` - way of preventing pings when a new video was deleted, must be at least 1
  - `threads` - how many concurrent tasks can run at once
- Guild configurations is a list of dictionaries with fields
  - `guild_id` - for which guild the config is made
  - `notifications_channel_id` - notification channel id (generally news channel)
  - `video_role_id` - role that will be pinged when a new `video` is released
  - `stream_role_id` - role that will be pinged when a new `stream` was started (unused)
  - `format`- how to format notification message string. Available keyword arguments:
    - `role_mention` - role that will be mentioned
    - `channel_name` - name of the channel that released a video/stream
    - `channel_url` - url link to channel
    - `channel_thumbnail_url` - url link to channel's thumbnail
    - `channel_country` - YouTube channel country
    - `video_url` - url link to a posted YouTube video
    - `video_title` - title of the posted video
    - `video_description` - description of the posted video
    - `video_thumbnail_url` - url link to video's thumbnail
    - `video_publish_date` - when the video was posted
    - There are also 2 subcategories
      - `text` - text used to make a message
      - `embed` - embed that will be sent with message
        - Contains 4 fields
          - `thumbnail` - embed url to thumbnail
          - `body` category
            - `title` - embed title
            - `description` - embed description
            - `url` - make title a clickable link
            - `color` - left chevron color
          - `author` category
            - `name` - author name
            - `url` - url to author
            - `icon_url` - url to icon
          - `fields` list category
            - `name` - field name
            - `value` - field value
  - `channels` - list of YouTube channel id's


# Config usage
- Config is used by module `YouTubeNotifs`
