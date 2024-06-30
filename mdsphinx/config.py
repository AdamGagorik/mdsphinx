import os
from pathlib import Path


CACHE: Path = Path(os.environ.get("MDSPHINX_SHELF", default=Path.home() / ".config" / "mdsphinx"))
SHELF: Path = CACHE / "environments.cache"
