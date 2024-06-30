import pytest

from mdsphinx.select import select


@pytest.mark.timeout(1)
def test_select_empty() -> None:
    assert select() == ()


@pytest.mark.timeout(1)
def test_select_simple() -> None:
    candidates = ("a", "b", "c")
    assert select(*candidates, query="a")[0] == "a"


@pytest.mark.timeout(1)
def test_select_with_complex() -> None:
    candidates = (("a", "x"), ("b", "y"), ("c", "z"))
    assert select(*candidates, headers=("h1", "h2"), matches=0, query="a")[0] == "a"
