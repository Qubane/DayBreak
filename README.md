# DayBreak
Discord bot based on `Qubane/MightyOmegaBot` project

# Dependencies
- Python 3.12 and above
- Packages listed in `requirements.txt`
- The `/latex` relies on [TexLive](https://www.tug.org/texlive/) or the following Linux packages:
  - `dvipng`
  - `texlive-latex-base`
  - `texlive-latex-extra`

# Functionality
- Moderation features
  - `/btimeout` - better timeout (proper time control, reason for timeout, user notification)
  - `/bkick` and `/bban` - better kick and better ban with user notification
  - `/warn` - warn system, after 3 warns the user is banned, and warns reset after 6 months, users get notified
- Random b#llshit features
  - `/latex` - LaTeX math equation rendering
  - `/bk` - prints `@user You like kissing boys don't you?`
  - `/morning-tea` - random local joke from 2020
- Random utils
  - `/latency` - bot latency
