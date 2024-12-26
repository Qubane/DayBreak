# `modules.json` file configuration
- Config file contains configurations for `TwitchNotifs` module
- The config is subdivided into 2 categories
  - `config` - global module configuration
  - `guild_config` - guild configurations
- Global module configuration has fields
  - `update_interval` - how often the update check is performed
  - `threads` - how many concurrent tasks can run at once
- Guild configurations is a list of dictionaries with fields
  - `guild_id` - for which guild the config is made
  - `notifications_channel_id` - notification channel id (generally news channel)
  - `role_id` - role that will be pinged when a notification is given
  - `format`- how to format notification message string. Available keyword arguments:
    - `role_mention` - role to ping
    - `channel_name` - channel that is now streaming
    - `stream_url` - url link to the stream
  - `channels` - list of twitch channel names


# Config usage
- Config is used by module `TwitchNotifs`
