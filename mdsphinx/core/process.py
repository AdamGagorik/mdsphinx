import dataclasses
import shutil
import webbrowser
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Annotated

import jinja2_mermaid_extension.base
from typer import Option

from mdsphinx.config import DEFAULT_ENVIRONMENT
from mdsphinx.config import LATEX_COMMAND
from mdsphinx.config import TMP_ROOT
from mdsphinx.core.environment import VirtualEnvironment
from mdsphinx.core.prepare import prepare
from mdsphinx.logger import logger
from mdsphinx.logger import run
from mdsphinx.tempdir import get_out_root
from mdsphinx.types import OptionalPath


class Format(Enum):
    pdf = "pdf"
    html = "html"
    confluence = "confluence"


@dataclasses.dataclass
class Builder:
    name: str
    output: Callable[[Path], Path] | None = None
    export: bool = False


def get_output(out_root: Path, *args: str, pattern: str) -> Path:
    for path in out_root.joinpath(*args).glob(pattern):
        return path
    raise FileNotFoundError(pattern)


LOOKUP_BUILDER: dict[Format, dict[str, Builder]] = {
    Format.pdf: {
        "latex": Builder(
            name="latex",
            output=lambda out_root: get_output(out_root, "build", "pdf", pattern="index.pdf"),
            export=True,
        ),
        "default": Builder(
            name="latex",
            output=lambda out_root: get_output(out_root, "build", "pdf", pattern="index.pdf"),
            export=True,
        ),
    },
    Format.html: {
        "html": Builder(
            name="html",
            output=lambda out_root: get_output(out_root, "build", "html", pattern="index.html"),
            export=False,
        ),
        "default": Builder(
            name="html",
            output=lambda out_root: get_output(out_root, "build", "html", pattern="index.html"),
            export=False,
        ),
        "single.page": Builder(
            name="singlehtml",
            output=lambda out_root: get_output(out_root, "build", "html", pattern="index.html"),
            export=False,
        ),
    },
    Format.confluence: {
        "default": Builder(
            name="confluence",
            output=None,
            export=False,
        ),
        "confluence": Builder(
            name="confluence",
            output=None,
            export=False,
        ),
        "single.page": Builder(
            name="singleconfluence",
            output=None,
            export=False,
        ),
    },
}


EPILOG = """
Examples

mdsphinx process example.md  --to pdf  --using latex --as example.pdf
mdsphinx process example.rst --to html --using default --as example.html
mdsphinx process ./directory --to html --using single-page --as example.html
""".replace(
    "\n", "\n\n"
)


def process(  # noqa: C901
    inp: Annotated[Path, "The input path or directory with markdown files."],
    format_key: Annotated[Format, Option("--to", help="The desired format.")] = Format.pdf,
    builder_key: Annotated[str, Option("--using", help="The desired builder.")] = "default",
    out: Annotated[OptionalPath, Option("--as", help="The desired builder.")] = None,
    env_name: Annotated[str, Option(help="The environment name.")] = DEFAULT_ENVIRONMENT,
    tmp_root: Annotated[Path, Option(help="The directory for temporary output.")] = TMP_ROOT,
    overwrite: Annotated[bool, Option(help="Force creation of new output folder in --tmp-root?")] = False,
    reconfigure: Annotated[bool, Option(help="Remove existing sphinx conf.py file?")] = False,
    show_output: Annotated[bool, Option(help="Open the generated output file?")] = False,
    just_build: Annotated[bool, Option(help="Just build the output without preparing the sources?")] = False,
) -> None:
    """
    Render markdown to the desired format.
    """
    inp = inp.resolve()
    tmp_root = tmp_root.resolve()
    out_root = get_out_root(inp.name, root=tmp_root)

    if not inp.exists():
        raise FileNotFoundError(inp)

    try:
        builder: Builder = LOOKUP_BUILDER[format_key][builder_key]
    except KeyError:
        raise KeyError(f"--using {builder_key} must be one of {', '.join(LOOKUP_BUILDER[format_key].keys())}")

    if not just_build:
        prepare(inp=inp, env_name=env_name, tmp_root=tmp_root, overwrite=overwrite, reconfigure=reconfigure)
        jinja2_mermaid_extension.base.runner().wait()

    if not out_root.joinpath("source").exists():
        raise FileNotFoundError(out_root)

    venv = VirtualEnvironment.from_db(env_name)

    # fmt: off
    venv.run(
        "sphinx-build",
        "-b",
        builder.name,
        out_root.joinpath("source"),
        out_root.joinpath("build", format_key.value),
    )
    # fmt: on

    if format_key == Format.pdf and builder.name == "latex":
        for command in LATEX_COMMAND:
            kwargs = dict(tex=get_output(out_root, "build", "pdf", pattern="index.tex"))
            run(*(part.format(**kwargs) for part in command))

    if out is not None:
        if builder.export and builder.output is not None:
            save_url(url=builder.output(out_root), out=out, top=tmp_root)
        else:
            logger.error(dict(action="save", message=f"Exporting {format_key.value} is not yet supported."))

    if show_output:
        if builder.output is not None:
            open_url(url=builder.output(out_root), top=tmp_root)
        else:
            raise NotImplementedError(f"Cant open {format_key.value} output.")


def open_url(url: Path, top: Path = TMP_ROOT) -> None:
    if url.exists():
        logger.info(dict(action="open", url=url if not url.is_relative_to(top) else url.relative_to(top)))
        webbrowser.open(url.as_uri(), new=2)
    else:
        raise FileNotFoundError(url)


def save_url(url: Path, out: Path, top: Path = TMP_ROOT) -> None:
    out = out.resolve()
    url = url if not url.is_relative_to(top) else url.relative_to(top)
    out = out if not out.is_relative_to(top) else out.relative_to(top)
    logger.info(dict(action="save", url=url, out=out))
    if url.exists():
        if out.is_dir():
            out = out.joinpath(url.name)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(url, out)
    else:
        raise FileNotFoundError(url)
