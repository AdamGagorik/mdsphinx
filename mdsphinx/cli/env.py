from pathlib import Path
from typing import Annotated

from typer import Typer

from mdsphinx import config
from mdsphinx.logger import logger


app = Typer(help="Manage environments.")


@app.command(name="add")
def add(
    name: Annotated[str, "The name of the environment."],
    path: Annotated[Path, "The virtual environment folder."],
) -> None:
    """
    Add a new environment to the registry.
    """
    raise NotImplementedError


@app.command(name="rename")
def rename(
    old: Annotated[str, "The old environment name."],
    new: Annotated[str, "The new environment name."],
) -> None:
    """
    Rename an environment in the registry.
    """
    raise NotImplementedError


@app.command(name="remove")
def remove(
    key: Annotated[str, "The name of the environment."],
    no_prompt: Annotated[bool, "Skip confirmation prompt?."],
) -> None:
    """
    Remove an environment from the registry.
    """
    raise NotImplementedError


@app.command(name="list")
def display() -> None:
    """
    List all environments in the registry.
    """
    logger.info(config.SHELF)


@app.command(name="create")
def create(
    key: Annotated[str, "The environment name."],
    path: Annotated[Path, "The virtual environment folder."],
) -> None:
    """
    Create a new virtual environment with the latest version of sphinx.
    """
    raise NotImplementedError
