import shutil
from enum import Enum
from pathlib import Path
from typing import Annotated

from typer import Argument
from typer import Option

from mdsphinx.config import TEMPLATE_ROOT


class Template(Enum):
    CONF_PY = "conf.py.jinja"


EPILOG = ""


def generate(
    name: Annotated[Template, Argument(help="Name of the template to generate.")],
    overwrite: Annotated[bool, Option("--overwrite", "-o", help="Overwrite the existing template?")] = False,
) -> None:
    """
    Generate a template for the Sphinx configuration file in the current directory.
    """
    output = Path.cwd().joinpath(name.value)
    if output.exists() and not overwrite:
        raise FileExistsError(output)

    shutil.copy(TEMPLATE_ROOT.joinpath(name.value), output)
