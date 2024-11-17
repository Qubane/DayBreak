import logging
import logging.handlers


logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    style="{",
    format="[{asctime}] [{levelname:<8}] {name}: {message}",
    handlers=[
        logging.handlers.RotatingFileHandler(
            filename="logs/discord.log",
            encoding="utf-8",
            maxBytes=2**20 * 32,  # 32 MiB
            backupCount=5),
        logging.StreamHandler()]
)
