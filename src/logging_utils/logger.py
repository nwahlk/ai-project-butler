import logging

from .formatters import DEBUG_LOG_FORMAT, DEFAULT_LOG_FORMAT


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def setup_logging(verbose: bool = False, debug: bool = False) -> None:
    if debug:
        level = logging.DEBUG
        log_format = DEBUG_LOG_FORMAT
    elif verbose:
        level = logging.INFO
        log_format = DEFAULT_LOG_FORMAT
    else:
        level = logging.WARNING
        log_format = DEFAULT_LOG_FORMAT

    logging.basicConfig(
        level=level,
        format=log_format,
        force=True,
    )
