import asyncio

from besteffort import yourmodule  # noqa: F401 ensures finder is installed


def test_example_raises_and_prints(capsys):
    yourmodule.example("Alice")
    captured = capsys.readouterr()
    assert "hi Alice" in captured.out
    assert "bye" in captured.out


def test_loops_stops_on_error(capsys):
    yourmodule.loops()
    captured = capsys.readouterr()
    assert "loop 0 start" in captured.out
    assert "loop 0 end" in captured.out
    assert "loop 1 start" in captured.out
    assert "loop 1 end" in captured.out
    assert "loop 2 start" in captured.out
    assert "loop 2 end" in captured.out
    assert "after loop" in captured.out


def test_tricky_raises_after_print(capsys):
    yourmodule.tricky()
    captured = capsys.readouterr()
    assert "before return" in captured.out
    assert "after return" in captured.out


def test_async_exception(capsys):
    async def run_async():
        await yourmodule.aex()

    asyncio.run(run_async())
    captured = capsys.readouterr()
    assert "astart" in captured.out
    assert "aend" in captured.out


def test_class_method_raises(capsys):
    instance = yourmodule.C()
    instance.m()
    captured = capsys.readouterr()
    assert "C.m before" in captured.out
    assert "C.m after" in captured.out
