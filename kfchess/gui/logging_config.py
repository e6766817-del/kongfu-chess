"""Configures the "kfchess.client" logger used across kfchess/gui/ to record
all client/server activity (connects, logins, room/matchmaking requests, and
every message sent/received) to both a file and the console."""

import logging

DEFAULT_LOG_PATH = "kfchess_client.log"

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(log_path=DEFAULT_LOG_PATH, level=logging.INFO):
    logger = logging.getLogger("kfchess.client")
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
