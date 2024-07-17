import json
import logging
import subprocess
from pathlib import Path
from typing import Any


logger = logging.getLogger("mdsphinx")


def run(
    *args: str | Path, action: str = "run", check: bool = True, echo: bool = True, **kwargs: Any
) -> subprocess.CompletedProcess[str]:
    if echo:
        logger.info(json.dumps(dict(action=action, command=tuple(map(str, args))), indent=2))
    return subprocess.run(args, check=check, **kwargs)
