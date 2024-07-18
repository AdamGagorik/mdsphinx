from enum import Enum
from pathlib import Path
from typing import Annotated

from typer import Option

from mdsphinx.config import DEFAULT_ENVIRONMENT
from mdsphinx.config import TMP_ROOT
from mdsphinx.core.environment import VirtualEnvironment
from mdsphinx.core.prepare import prepare
from mdsphinx.logger import run
from mdsphinx.tempdir import get_out_root


class Output(Enum):
    pdf = "pdf"
    html = "html"
    confluence = "confluence"


LOOKUP_BUILDER: dict[Output, str] = {
    Output.pdf: "latex",
    Output.html: "html",
    Output.confluence: "confluence",
}


def process(
    inp: Annotated[Path, "The input path or directory with markdown files."],
    to: Annotated[Output, Option(help="The desired output format.")] = Output.pdf,
    env_name: Annotated[str, Option(help="The environment name.")] = DEFAULT_ENVIRONMENT,
    tmp_root: Annotated[Path, Option(help="The directory for temporary output.")] = TMP_ROOT,
    overwrite: Annotated[bool, Option(help="Force creation of new output folder in --tmp-root?")] = False,
) -> None:
    """
    Render markdown to the desired format.
    """
    inp = inp.resolve()
    tmp_root = tmp_root.resolve()
    out_root = get_out_root(inp.name, root=tmp_root)

    if not inp.exists():
        raise FileNotFoundError(inp)

    prepare(inp=inp, env_name=env_name, tmp_root=tmp_root, overwrite=overwrite)

    venv = VirtualEnvironment.from_db(env_name)

    # fmt: off
    venv.run(
        "sphinx-build",
        "-b",
        LOOKUP_BUILDER[to],
        out_root.joinpath("source"),
        out_root.joinpath("build", to.value),
    )
    # fmt: on

    if to == Output.pdf:
        run("tectonic", out_root.joinpath("build", to.value, "mdsphinx.tex"))
