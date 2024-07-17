import shelve
import shutil
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from subprocess import run
from typing import Annotated
from typing import Optional

from typer import confirm
from typer import Option
from typer import Typer

from mdsphinx.config import DEFAULT_ENVIRONMENT
from mdsphinx.config import DEFAULT_ENVIRONMENT_PACKAGES
from mdsphinx.config import ENVIRONMENTS
from mdsphinx.config import ENVIRONMENTS_REGISTRY
from mdsphinx.logger import logger


MultipleStrings = Optional[list[str]]


app = Typer(help="Manage environments.")


@contextmanager
def environments() -> Generator[shelve.Shelf[Path], None, None]:
    with shelve.open(str(ENVIRONMENTS_REGISTRY), writeback=True) as shelf:
        yield shelf


@app.command(name="add")
def add_env(
    name: Annotated[str, Option(help="The name of the environment.")],
    path: Annotated[Path, Option(help="The virtual environment folder.")],
) -> None:
    """
    Add a new environment to the registry.
    """
    with environments() as db:
        if name in db:
            logger.warning(dict(action="add", name=name, message="overwriting environment"))

        logger.info(dict(action="add", name=name))
        db[name] = path


@app.command(name="del")
def del_env(
    name: Annotated[str, Option(help="The name of the environment.")],
) -> None:
    """
    Remove an environment from the registry.
    """
    with environments() as db:
        if name in db:
            logger.info(dict(action="del", name=name))
            del db[name]
        else:
            logger.warning(dict(action="del", name=name, message="environment not found"))


@app.command(name="list")
def display_envs() -> None:
    """
    List all environments in the registry.
    """
    with environments() as db:
        if db:
            for i, (name, path) in enumerate(db.items()):
                logger.info(dict(action="list", index=i, name=name, path=path))
        else:
            logger.warning(dict(action="list", message="no environments found"))


@app.command(name="create")
def create_env(
    name: Annotated[str, Option(help="The environment name.")] = DEFAULT_ENVIRONMENT,
    python: Annotated[Path, Option(help="The python executable.")] = Path(sys.executable),
    packages: Annotated[MultipleStrings, Option("--package", help="Extra packages to install.")] = None,
    recreate: Annotated[bool, Option(help="Recreate the environment?")] = False,
    prompt: Annotated[bool, Option(help="Prompt for removal?")] = True,
) -> None:
    """
    Create a new virtual environment with the latest version of sphinx.
    """
    path = ENVIRONMENTS / f"venv.{name}"
    if path.exists():
        if recreate:
            if not remove_env(name, prompt=prompt):
                return
        else:
            logger.error(dict(action="create", name=name, path=path, message="environment already exists"))
            return

    vpython = path / "bin" / "python"
    path.parent.mkdir(parents=True, exist_ok=True)

    def echo_run(*args: str) -> None:
        logger.info(dict(action="run", name=name, command=" ".join(args)))
        run(args, check=True)

    # noinspection PyBroadException
    try:
        echo_run(str(python), "-m", "venv", str(path))
        echo_run(str(vpython), "-m", "pip", "install", "pip", "--upgrade")
        echo_run(str(vpython), "-m", "pip", "install", "sphinx", "--upgrade")
        for package in packages if packages is not None else DEFAULT_ENVIRONMENT_PACKAGES:
            echo_run(str(vpython), "-m", "pip", "install", package, "--upgrade")
    except Exception:
        logger.exception(dict(action="create", name=name, message="unhandled exception"))
        remove_env(name, prompt=False)

    add_env(name, path)


@app.command(name="remove")
def remove_env(
    name: Annotated[str, Option(help="The environment name.")],
    prompt: Annotated[bool, Option(help="Prompt for removal?")] = True,
) -> bool:
    """
    Remove an existing environment that was created by mdsphinx.
    """
    path = ENVIRONMENTS / f"venv.{name}"
    if path.exists():
        if not prompt or confirm(f"Remove {path}?", default=False):
            logger.info(dict(action="remove", name=name, path=path, message="removing environment"))
            shutil.rmtree(path)
            del_env(name)
            return True
        else:
            logger.error(dict(action="remove", name=name, path=path, message="operation cancelled"))
            return False
    else:
        logger.error(dict(action="remove", name=name, path=path, message="environment not found"))
        return False
