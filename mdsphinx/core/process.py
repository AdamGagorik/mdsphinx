import webbrowser
from enum import Enum
from pathlib import Path
from typing import Annotated

from typer import Option

from mdsphinx.config import DEFAULT_ENVIRONMENT
from mdsphinx.config import LATEX_COMMAND
from mdsphinx.config import TMP_ROOT
from mdsphinx.core.environment import VirtualEnvironment
from mdsphinx.core.prepare import prepare
from mdsphinx.logger import logger
from mdsphinx.logger import run
from mdsphinx.tempdir import get_out_root


class Format(Enum):
    pdf = "pdf"
    html = "html"
    confluence = "confluence"


LOOKUP_BUILDER: dict[Format, dict[str, str]] = {
    Format.pdf: {"latex": "latex", "default": "latex"},
    Format.html: {
        "html": "html",
        "default": "html",
        "single-page": "singlehtml",
    },
    Format.confluence: {"default": "confluence", "confluence": "confluence", "single-page": "singleconfluence"},
}


def process(
    inp: Annotated[Path, "The input path or directory with markdown files."],
    format_key: Annotated[Format, Option("--to", help="The desired format.")] = Format.pdf,
    builder_key: Annotated[str, Option("--using", help="The desired builder.")] = "default",
    env_name: Annotated[str, Option(help="The environment name.")] = DEFAULT_ENVIRONMENT,
    tmp_root: Annotated[Path, Option(help="The directory for temporary output.")] = TMP_ROOT,
    overwrite: Annotated[bool, Option(help="Force creation of new output folder in --tmp-root?")] = False,
    reconfigure: Annotated[bool, Option(help="Remove existing sphinx conf.py file?")] = False,
    show_output: Annotated[bool, Option(help="Open the generated output file?")] = False,
) -> None:
    """
    Render markdown to the desired format.

    Example:
        mdsphinx process example.md  --to pdf  --using latex --show-output
        mdsphinx process example.rst --to html --using default --show-output
        mdsphinx process ./directory --to html --using single-page --show-output
    """
    inp = inp.resolve()
    tmp_root = tmp_root.resolve()
    out_root = get_out_root(inp.name, root=tmp_root)

    if not inp.exists():
        raise FileNotFoundError(inp)

    try:
        builder = LOOKUP_BUILDER[format_key][builder_key]
    except KeyError:
        raise KeyError(f"--using {builder_key} must be one of {', '.join(LOOKUP_BUILDER[format_key].keys())}")

    prepare(inp=inp, env_name=env_name, tmp_root=tmp_root, overwrite=overwrite, reconfigure=reconfigure)

    venv = VirtualEnvironment.from_db(env_name)

    # fmt: off
    venv.run(
        "sphinx-build",
        "-b",
        builder,
        out_root.joinpath("source"),
        out_root.joinpath("build", format_key.value),
    )
    # fmt: on

    if format_key == Format.pdf and builder == "latex":
        for command in LATEX_COMMAND:
            kwargs = dict(tex=get_input_tex(out_root, format_key))
            run(*(part.format(**kwargs) for part in command))

    if show_output:
        match format_key:
            case Format.pdf:
                open_url(get_output_pdf(out_root, format_key))
            case Format.html:
                open_url(get_output_html(out_root, format_key))
            case _:
                raise NotImplementedError(f"Cant open {format_key.value} output.")


def open_url(url: Path) -> None:
    logger.info(dict(action="open", url=url))
    if url.exists():
        logger.info(dict(action="open", url=url))
        webbrowser.open(url.as_uri(), new=2)
    else:
        raise FileNotFoundError(url)


def get_input_tex(out_root: Path, format_key: Format) -> Path:
    for path in out_root.joinpath("build", format_key.value).glob("index.tex"):
        return path
    raise FileNotFoundError("*.tex")


def get_output_pdf(out_root: Path, format_key: Format) -> Path:
    for path in out_root.joinpath("build", format_key.value).glob("index.pdf"):
        return path
    raise FileNotFoundError("*.pdf")


def get_output_html(out_root: Path, format_key: Format) -> Path:
    for path in out_root.joinpath("build", format_key.value).glob("index.html"):
        return path
    raise FileNotFoundError("*.html")
