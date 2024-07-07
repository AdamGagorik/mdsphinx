import logging

from typer import Typer

import mdsphinx.cli.environment
import mdsphinx.cli.prepare
import mdsphinx.cli.process


app = Typer(add_completion=False)


@app.callback()
def cb(verbose: bool = False) -> None:
    """
    Convert markdown to any output format that Sphinx supports.
    """
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="%(levelname)-8s | %(message)s")


app.add_typer(mdsphinx.cli.environment.app, name="env")
app.command()(mdsphinx.cli.prepare.prepare)
app.command()(mdsphinx.cli.process.process)


if __name__ == "__main__":
    app()
