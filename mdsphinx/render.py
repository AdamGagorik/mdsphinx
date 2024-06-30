from enum import Enum
from pathlib import Path
from typing import Annotated

from typer import Typer

from mdsphinx.logger import logger


app = Typer(help="Manage environments.")


class Builder(Enum):
    pdf = "pdf"
    html = "html"
    latex = "latex"
    single_html = "single.html"
    confluence_page = "confluence.page"
    single_confluence_page = "single.confluence"


@app.command(name="pdf")
def render_pdf(
    inp: Annotated[Path, "The input path or directory"],
    out: Annotated[Path, "The output path or directory"],
) -> None:
    """
    Render markdown as a PDF.
    """
    logger.info("Rendering PDF")


@app.command(name="html")
def render_html(
    inp: Annotated[Path, "The input path or directory"],
    out: Annotated[Path, "The output path or directory"],
) -> None:
    """
    Render markdown as HTML.
    """
    logger.info("Rendering HTML")


@app.command(name="confluence")
def render_confluence(
    inp: Annotated[Path, "The input path or directory"],
    out: Annotated[Path, "The output path or directory"],
) -> None:
    """
    Render markdown as Confluence pages.
    """
    logger.info("Rendering Confluence pages")
