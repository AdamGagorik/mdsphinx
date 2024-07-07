from enum import Enum
from pathlib import Path
from typing import Annotated

from typer import Option

from mdsphinx.core.prepare import prepare
from mdsphinx.logger import logger
from mdsphinx.tempdir import get_out_root
from mdsphinx.tempdir import TMP_ROOT


class Builder(Enum):
    pdf = "pdf"
    html = "html"
    latex = "latex"
    confluence_page = "confluence"


def process(
    inp: Annotated[Path, "The input path or directory with markdown files."],
    to: Annotated[Builder, Option(help="The desired output format.")] = Builder.pdf,
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

    prepare(inp=inp, tmp_root=tmp_root, overwrite=overwrite)
