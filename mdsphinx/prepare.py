from pathlib import Path
from typing import Annotated

from mdsphinx.logger import logger


def prepare(
    inp: Annotated[Path, "The input path or directory."],
) -> None:
    """
    Preprocess the input files.
    """
    logger.info("Preparing the input files.")
