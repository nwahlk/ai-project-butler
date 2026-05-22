import logging

from logging_config import setup_logging as legacy_setup_logging
from logging_utils import get_logger, setup_logging
from logging_utils.formatters import DEBUG_LOG_FORMAT, DEFAULT_LOG_FORMAT


def test_setup_logging_defaults_to_warning_level():
    setup_logging()

    assert logging.getLogger().level == logging.WARNING
    assert logging.getLogger("project").isEnabledFor(logging.INFO) is False


def test_setup_logging_verbose_enables_info_level():
    setup_logging(verbose=True)

    assert logging.getLogger().level == logging.INFO
    assert logging.getLogger("project").isEnabledFor(logging.INFO) is True


def test_setup_logging_debug_enables_debug_format():
    setup_logging(debug=True)

    handler = logging.getLogger().handlers[0]

    assert logging.getLogger().level == logging.DEBUG
    assert handler.formatter is not None
    assert handler.formatter._fmt == DEBUG_LOG_FORMAT


def test_get_logger_delegates_to_standard_logging():
    logger = get_logger("project.test")

    assert logger is logging.getLogger("project.test")


def test_legacy_logging_config_reexports_setup_logging():
    legacy_setup_logging(verbose=True)

    handler = logging.getLogger().handlers[0]

    assert logging.getLogger().level == logging.INFO
    assert handler.formatter is not None
    assert handler.formatter._fmt == DEFAULT_LOG_FORMAT
