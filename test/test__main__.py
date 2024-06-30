import pytest
from typer.testing import CliRunner

from mdsphinx.cli.__main__ import app


@pytest.mark.parametrize(
    "args",
    [
        pytest.param(("env", "add", "--help"), id="mdsphinx env add"),
        pytest.param(("env", "rename", "--help"), id="mdsphinx env rename"),
        pytest.param(("env", "remove", "--help"), id="mdsphinx env remove"),
        pytest.param(("env", "list", "--help"), id="mdsphinx env list"),
        pytest.param(("env", "create", "--help"), id="mdsphinx env create"),
        pytest.param(("prepare", "--help"), id="mdsphinx prepare"),
        pytest.param(("render", "pdf", "--help"), id="mdsphinx render pdf"),
        pytest.param(("render", "html", "--help"), id="mdsphinx render html"),
        pytest.param(("render", "confluence", "--help"), id="mdsphinx render confluence"),
    ],
)
def test_app(args: tuple[str, ...]) -> None:
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0
