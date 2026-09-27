"""Unit tests for app.utils.timing module."""

import time
from app.utils.timing import timer


def test_timer(capsys):
    with timer("test block"):
        time.sleep(0.01)

    captured = capsys.readouterr()
    assert "[timer] test block:" in captured.out
    assert "ms" in captured.out
