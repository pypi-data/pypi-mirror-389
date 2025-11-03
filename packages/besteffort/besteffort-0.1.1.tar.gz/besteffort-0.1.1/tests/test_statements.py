import asyncio
import sys

import pytest

from besteffort import statements_module


def test_try_finally_all_statements_execute():
    result = statements_module.try_finally_example()
    assert result == [
        "try start",
        "try end",
        "finally block",
        "after try",
    ]


def test_while_else_continues_after_errors():
    result = statements_module.while_else_example()
    assert result == [
        "while 0 start",
        "while 0 end",
        "while 1 start",
        "while 1 end",
        "while 2 start",
        "while 2 end",
        "while else",
        "after while",
    ]


def test_with_body_continues():
    result = statements_module.with_example()
    assert result == [
        "with start",
        "with end",
        "after with",
    ]


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+ for match")
def test_match_case_is_instrumented():
    from besteffort import statements_match

    result = statements_match.match_example("alpha")
    assert result == [
        "match alpha start",
        "match alpha end",
        "after match",
    ]


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires Python 3.11+ for exception groups")
def test_trystar_body_is_wrapped():
    from besteffort import statements_trystar

    result = statements_trystar.trystar_example()
    assert result == [
        "trystar start",
        "trystar end",
        "trystar finally",
        "trystar after",
    ]


def test_async_with_is_instrumented():
    result = asyncio.run(statements_module.async_with_example())
    assert result == [
        "async with start",
        "async with end",
        "async with after",
    ]


def test_async_for_continues_iteration():
    result = asyncio.run(statements_module.async_for_example())
    assert result == [
        "async for 0 start",
        "async for 0 end",
        "async for 1 start",
        "async for 1 end",
        "async for 2 start",
        "async for 2 end",
        "async for done",
    ]
