from __future__ import annotations

import shelve
import shutil
import sys
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from subprocess import CompletedProcess
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
from mdsphinx.logger import run


MultipleStrings = Optional[list[str]]


app = Typer(help="Manage environments.")


@dataclass
class VirtualEnvironment:
    name: str
    path: Path

    @classmethod
    def from_db(cls, name: str) -> VirtualEnvironment:
        with environments() as db:
            venv = cls(name, db[name])
            logger.info(f"venv.name: {venv.name}")
            logger.info(f"venv.path: {venv.path}")
            return venv

    @classmethod
    def from_name(cls, name: str) -> VirtualEnvironment:
        return cls(name, ENVIRONMENTS / f"venv.{name}")

    @property
    def python(self) -> Path:
        return self.path / "bin" / "python"

    def run(self, command: str | Path, *args: str | Path) -> CompletedProcess[str]:
        return run(str(self.path / "bin" / command), *args)

    def pyrun(self, package: str | Path, *args: str | Path) -> CompletedProcess[str]:
        return run(str(self.python), "-m", package, *args)

    def create(self, base_python: Path, recreate: bool = False, prompt: bool = True) -> bool:
        if self.path.exists():
            if recreate:
                if not self.remove(prompt=prompt):
                    return False
            else:
                logger.error(dict(action="create", name=self.name, path=self.path, message="environment already exists"))
                return False

        self.path.parent.mkdir(parents=True, exist_ok=True)
        return not bool(run(str(base_python), "-m", "venv", str(self.path)).returncode)

    def remove(self, prompt: bool = True) -> bool:
        if self.path.exists():
            if not prompt or confirm(f"Remove {self.path}?", default=False):
                logger.info(dict(action="remove", name=self.name, path=self.path, message="removing environment"))
                shutil.rmtree(self.path)
                del_env(self.name)
                return True
            else:
                logger.error(dict(action="remove", name=self.name, path=self.path, message="operation cancelled"))
                return False
        else:
            logger.error(dict(action="remove", name=self.name, path=self.path, message="environment not found"))
            return False

    def install(self, package: str) -> None:
        self.pyrun("pip", "install", package, "--upgrade")


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
    venv = VirtualEnvironment.from_name(name)
    if not venv.create(python, recreate=recreate, prompt=prompt):
        return

    # noinspection PyBroadException
    try:
        venv.install("pip")
        venv.install("sphinx")
        for package in packages if packages is not None else DEFAULT_ENVIRONMENT_PACKAGES:
            venv.install(package)
    except Exception:
        logger.exception(dict(action="create", name=name, message="unhandled exception"))
        venv.remove(prompt=False)

    add_env(name, venv.path)


@app.command(name="remove")
def remove_env(
    name: Annotated[str, Option(help="The environment name.")] = DEFAULT_ENVIRONMENT,
    prompt: Annotated[bool, Option(help="Prompt for removal?")] = True,
) -> bool:
    """
    Remove an existing environment that was created by mdsphinx.
    """
    return VirtualEnvironment.from_name(name).remove(prompt=prompt)
