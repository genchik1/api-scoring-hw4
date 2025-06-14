import logging
from typing import Any

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"


def set_logging_settings(log_filename: str) -> None:
    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )


def get_logger(name: str | None = None) -> Any:
    return logging.getLogger(name)
