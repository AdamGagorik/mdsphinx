import json
import logging
import subprocess
from pathlib import Path
from typing import Any


logger = logging.getLogger("mdsphinx")


def run(*args: str | Path, action: str = "run", **kwargs: Any) -> None:
    logger.info(json.dumps(dict(action=action, command=args), indent=2))
    subprocess.run(args, **(dict(check=True) | kwargs))
