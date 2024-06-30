from datetime import datetime
from datetime import UTC
from pathlib import Path

import pytest

from mdsphinx.tempdir import find_latest_directory
from mdsphinx.tempdir import make_next_directory


dt = datetime.now(UTC)


@pytest.mark.parametrize(
    "existing,expected",
    [
        pytest.param([], f"key.{dt:%Y-%m-%d}.0", id="empty"),
        pytest.param([f"key.{dt:%Y-%m-%d}.abcde.0"], f"key.{dt:%Y-%m-%d}.abcde.1", id="single"),
    ],
)
def test_make_next_directory(existing: tuple[str], expected: str, tmp_path: Path) -> None:
    for name in existing:
        (tmp_path / name).mkdir(exist_ok=True, parents=True)

    observed: Path = make_next_directory("key", root=tmp_path)
    assert observed.name.startswith(f"key.{dt:%Y-%m-%d}.")
    assert observed.name.endswith(expected.split(".")[-1])


@pytest.mark.parametrize(
    "existing,expected",
    [
        pytest.param([], FileNotFoundError, id="empty"),
        pytest.param([f"key.{dt:%Y-%m-%d}.abcde.0"], f"key.{dt:%Y-%m-%d}.abcde.0", id="single"),
    ],
)
def test_find_latext_keyed_directory(existing: tuple[str], expected: str | type[Exception], tmp_path: Path) -> None:
    for name in existing:
        (tmp_path / name).mkdir(exist_ok=True, parents=True)

    if isinstance(expected, str):
        observed: Path = find_latest_directory("key", root=tmp_path)
        assert observed == tmp_path / expected
    else:
        with pytest.raises(expected):
            find_latest_directory("key", root=tmp_path)
