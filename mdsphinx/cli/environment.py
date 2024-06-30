import shelve
import shutil
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from subprocess import run
from typing import Annotated

from typer import confirm
from typer import Option
from typer import Typer

from mdsphinx.config import ENVIRONMENTS
from mdsphinx.config import ENVIRONMENTS_REGISTRY
from mdsphinx.logger import logger


app = Typer(help="Manage environments.")


@contextmanager
def environments() -> Generator[shelve.Shelf[Path], None, None]:
    with shelve.open(str(ENVIRONMENTS_REGISTRY), writeback=True) as shelf:
        yield shelf


@app.command(name="add")
def add_env(
    key: Annotated[str, "The name of the environment."],
    path: Annotated[Path, "The virtual environment folder."],
) -> None:
    """
    Add a new environment to the registry.
    """
    with environments() as db:
        if key in db:
            logger.warning(dict(action="add", key=key, message="overwriting key"))

        logger.info(dict(action="add", key=key))
        db[key] = path


@app.command(name="del")
def del_env(
    key: Annotated[str, "The name of the environment."],
) -> None:
    """
    Remove an environment from the registry.
    """
    with environments() as db:
        if key in db:
            logger.info(dict(action="del", key=key))
            del db[key]
        else:
            logger.warning(dict(action="del", key=key, message="key not found"))


@app.command(name="list")
def display_envs() -> None:
    """
    List all environments in the registry.
    """
    with environments() as db:
        if db:
            for i, (key, path) in enumerate(db.items()):
                logger.info(dict(action="list", index=i, key=key, path=path))
        else:
            logger.warning(dict(action="list", message="no environments found"))


@app.command(name="create")
def create_env(
    key: Annotated[str, "The environment name."],
    python: Annotated[Path, Option(help="The python executable.")] = Path(sys.executable),
    recreate: Annotated[bool, Option(help="Recreate the environment?")] = False,
) -> None:
    """
    Create a new virtual environment with the latest version of sphinx.
    """
    path = ENVIRONMENTS / f"venv.{key}"
    if path.exists():
        if recreate:
            if not remove_env(key):
                return
        else:
            logger.error(dict(action="create", key=key, path=path, message="environment already exists"))
            return

    vpython = path / "bin" / "python"
    path.parent.mkdir(parents=True, exist_ok=True)

    # noinspection PyBroadException
    try:
        run([str(python), "-m", "venv", str(path)], check=True)
        run([str(vpython), "-m", "pip", "install", "pip", "--upgrade"], check=True)
        run([str(vpython), "-m", "pip", "install", "sphinx", "--upgrade"], check=True)
    except Exception:
        logger.exception(dict(action="create", key=key, message="unhandled exception"))
        remove_env(key)

    add_env(key, path)


@app.command(name="remove")
def remove_env(
    key: Annotated[str, "The environment name."],
) -> bool:
    """
    Remove an existing environment that was created by mdsphinx.
    """
    path = ENVIRONMENTS / f"venv.{key}"
    if path.exists():
        if confirm(f"Remove {path}?", default=False):
            logger.info(dict(action="remove", key=key, path=path, message="removing environment"))
            shutil.rmtree(path)
            del_env(key)
            return True
        else:
            logger.error(dict(action="remove", key=key, path=path, message="operation cancelled"))
            return False
    else:
        logger.error(dict(action="remove", key=key, path=path, message="environment not found"))
        return False
