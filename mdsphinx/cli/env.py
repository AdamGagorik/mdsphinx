import sys
from pathlib import Path
from typing import Annotated

from typer import Option
from typer import Typer


app = Typer(help="Manage environments.")


@app.command(name="add")
def add_env_cli(
    key: Annotated[str, "The name of the environment."],
    path: Annotated[Path, "The virtual environment folder."],
) -> None:
    """
    Add a new environment to the registry.
    """
    from mdsphinx.core.env import add_env

    add_env(key, path)


@app.command(name="del")
def del_env_cli(
    key: Annotated[str, "The name of the environment."],
) -> None:
    """
    Remove an environment from the registry.
    """
    from mdsphinx.core.env import del_env

    del_env(key)


@app.command(name="list")
def display_envs_cli() -> None:
    """
    List all environments in the registry.
    """
    from mdsphinx.core.env import display_envs

    display_envs()


@app.command(name="create")
def create_env_cli(
    key: Annotated[str, "The environment name."],
    python: Annotated[Path, Option(help="The python executable.")] = Path(sys.executable),
    recreate: Annotated[bool, Option(help="Recreate the environment?")] = False,
) -> None:
    """
    Create a new virtual environment with the latest version of sphinx.
    """
    from mdsphinx.core.env import create_env

    create_env(key, python, recreate)
