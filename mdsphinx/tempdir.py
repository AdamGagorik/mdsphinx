import re
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from tempfile import mkdtemp

from mdsphinx.config import TMP_ROOT


def get_out_root(key: str, root: Path = TMP_ROOT, overwrite: bool = False) -> Path:
    try:
        if overwrite:
            return make_next_directory(key, root=root)
        return find_latest_directory(key, root=root)
    except FileNotFoundError:
        return make_next_directory(key, root=root)


def make_next_directory(key: str, root: Path = TMP_ROOT) -> Path:
    try:
        latest = int(find_latest_directory(key, root=root).name.split(".")[-1])
    except FileNotFoundError:
        latest = -1

    return Path(mkdtemp(prefix=f"{key}.{datetime.now():%Y-%m-%d}.", suffix=f".{latest + 1:}", dir=root))


def find_latest_directory(key: str, root: Path = TMP_ROOT) -> Path:
    def _() -> Generator[tuple[datetime, int, Path], None, None]:
        for path in root.glob(f"{key}.*"):
            if match := re.match(rf"{key}\.(?P<DT>\d\d\d\d-\d\d-\d\d)\..*?\.(?P<ID>\d)", path.name):
                yield datetime.strptime(match.group("DT"), "%Y-%m-%d"), int(match.group("ID")), path

    if found := sorted(_(), key=lambda t: (t[0], t[1])):
        return found[-1][2]
    else:
        raise FileNotFoundError(f"{key}.* not found in {root}")
