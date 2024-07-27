import logging

from typer import Typer

import mdsphinx.core.environment
import mdsphinx.core.prepare
import mdsphinx.core.process


app = Typer(add_completion=False)


@app.callback()
def cb(verbose: bool = False) -> None:
    """
    Convert markdown to any output format that Sphinx supports.
    """
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)-8s | %(message)s")


app.add_typer(mdsphinx.core.environment.app, name="env")
app.command()(mdsphinx.core.prepare.prepare)
app.command()(mdsphinx.core.process.process)


if __name__ == "__main__":
    app()
