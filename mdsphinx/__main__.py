import logging

from typer import Exit
from typer import Typer

import mdsphinx.core.environment
import mdsphinx.core.generate
import mdsphinx.core.prepare
import mdsphinx.core.process


app = Typer(add_completion=False, rich_markup_mode="rich", invoke_without_command=True)


app.add_typer(mdsphinx.core.environment.app, name="env")
app.command(epilog=mdsphinx.core.prepare.EPILOG)(mdsphinx.core.prepare.prepare)
app.command(epilog=mdsphinx.core.process.EPILOG)(mdsphinx.core.process.process)
app.command(epilog=mdsphinx.core.generate.EPILOG)(mdsphinx.core.generate.generate)


@app.callback()
def cb(version: bool = False, verbose: bool = False) -> None:
    """
    Convert markdown to any output format that Sphinx supports.
    """
    if version:
        from mdsphinx import __version__

        print(__version__)
        raise Exit(0)

    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)-8s | %(message)s")


if __name__ == "__main__":
    app()
