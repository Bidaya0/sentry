import logging
from typing import Any
from unittest import mock

import pytest

from sentry.logging.handlers import StructLogHandler


@pytest.fixture
def handler():
    return StructLogHandler()


@pytest.fixture
def logger():
    return mock.MagicMock()


def make_logrecord(
    *,
    name: str = "name",
    level: int = logging.INFO,
    pathname: str = "pathname",
    lineno: int = 10,
    msg: str = "msg",
    args: Any = None,
    exc_info: Any = None,
    **extra: Any,
) -> logging.LogRecord:
    return logging.LogRecord(
        name=name,
        level=level,
        pathname=pathname,
        lineno=lineno,
        msg=msg,
        args=args,
        exc_info=exc_info,
        **extra,
    )


@pytest.mark.parametrize(
    "record,out",
    (
        ({}, {}),
        ({"msg": "%s", "args": (1,)}, {"event": "%s", "positional_args": (1,)}),
        ({"args": ({"a": 1},)}, {"positional_args": ({"a": 1},)}),
        ({"exc_info": True}, {"exc_info": True}),
    ),
)
def test_emit(record, out, handler, logger):
    record = make_logrecord(**record)
    handler.emit(record, logger=logger)
    expected = dict(level=logging.INFO, event="msg", name="name")
    expected.update(out)
    logger.log.assert_called_once_with(**expected)


@mock.patch("sentry.logging.handlers.metrics")
def test_log_to_metric(metrics):
    logger = logging.getLogger("django.request")
    logger.warning("CSRF problem")
    metrics.incr.assert_called_once_with("django.request.csrf_problem", skip_internal=False)

    metrics.reset_mock()

    logger.warning("Some other problem we don't care about")
    assert metrics.incr.call_count == 0
