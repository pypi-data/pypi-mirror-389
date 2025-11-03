import asyncio
from typing import List

import pytest

from besteffort import besteffort


def test_decorator_suppresses_exceptions(capsys):
    @besteffort
    def sample(name: str, calls: List[str]) -> None:
        print(f"start {name}")
        calls.append("before")
        raise ValueError("boom")
        print(f"end {name}")
        calls.append("after")

    calls: List[str] = []
    sample("x", calls)
    captured = capsys.readouterr()
    assert "start x" in captured.out
    assert "end x" in captured.out
    assert calls == ["before", "after"]


def test_decorator_handles_async_functions(capsys):
    @besteffort
    async def sample_async(seen: List[int]) -> None:
        print("async start")
        seen.append(1)
        raise RuntimeError("bad async")
        print("async end")
        seen.append(2)

    seen: List[int] = []
    asyncio.run(sample_async(seen))
    captured = capsys.readouterr()
    assert "async start" in captured.out
    assert "async end" in captured.out
    assert seen == [1, 2]


def test_decorator_leaves_other_functions_untouched():
    @besteffort
    def sample(x: int) -> int:
        if x == 0:
            raise ValueError("x cannot be zero")
        return 10 // x

    assert sample(2) == 5
    def normal(x: int) -> int:
        return 10 // x

    assert normal(2) == 5
    with pytest.raises(ZeroDivisionError):
        normal(0)
