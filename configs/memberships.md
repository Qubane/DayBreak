# `memberships.json` file configuration
- Config file contains information about which guilds have which roles considered "member roles"
- To configure memberships edit file `memberships.json`
- File consists of a dictionary where `key` is `guild_id` and `value` is `role_id`
    - `"guild_id": "role_id"`
- Append another line with your own `guild_id` and `role_id` to configure memberships

# Config usage
- Config is used by static module `BotUtils`
