import logging
import sys
from os import environ

from mybot import MyBot
from utils.db import db
from utils.logger import create_logger

logger = create_logger(level=getattr(logging, environ.get("LOG_LEVEL", "INFO")))
logging.getLogger("discord").setLevel(logging.INFO)


def main():
    mybot: MyBot = MyBot(db)

    try:
        mybot.run(environ["BOT_TOKEN"], reconnect=True, log_handler=None)
    except KeyError as e:
        logger.critical(f"Missing environment variable {e}.")
        sys.exit(1)


if __name__ == "__main__":
    main()
