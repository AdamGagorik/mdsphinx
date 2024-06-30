import shelve
import shutil
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from subprocess import run

from typer import confirm

from mdsphinx.config import ENVIRONMENTS
from mdsphinx.config import ENVIRONMENTS_REGISTRY
from mdsphinx.logger import logger


@contextmanager
def environments() -> Generator[shelve.Shelf[Path], None, None]:
    with shelve.open(str(ENVIRONMENTS_REGISTRY), writeback=True) as shelf:
        yield shelf


def add_env(key: str, path: Path) -> None:
    with environments() as db:
        if key in db:
            logger.warning(dict(action="add", key=key, message="overwriting key"))

        logger.info(dict(action="add", key=key))
        db[key] = path


def del_env(key: str) -> None:
    with environments() as db:
        if key in db:
            logger.info(dict(action="del", key=key))
            del db[key]
        else:
            logger.warning(dict(action="del", key=key, message="key not found"))


def display_envs() -> None:
    with environments() as db:
        if db:
            for i, (key, path) in enumerate(db.items()):
                logger.info(dict(action="list", index=i, key=key, path=path))
        else:
            logger.warning(dict(action="list", message="no environments found"))


def create_env(key: str, python: Path, recreate: bool) -> None:
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


def remove_env(key: str) -> bool:
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
