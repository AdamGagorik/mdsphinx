import inspect
import shutil
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from jinja2 import Environment

from mdsphinx.jinjaext import GenImageExtension
from mdsphinx.logger import run


def mermaid(
    inp: Path | str,
    out: Path,
    theme: str = "default",
    scale: int = 3,
    width: int = 800,
    height: int | None = None,
    background_color: str = "white",
) -> None:
    """
    Generate a mermaid diagram from a mermaid code block or input file.
    """
    with TemporaryDirectory() as tmp_root:
        if isinstance(inp, str):
            tmp_inp = Path(tmp_root) / out.with_suffix(".mmd").name
            with tmp_inp.open("w") as stream:
                stream.write(inp)
        else:
            tmp_inp = Path(tmp_root) / inp.name
            shutil.copy(inp, tmp_inp)

        tmp_out = Path(tmp_root) / out.name
        if tmp_out.exists():
            raise FileExistsError(tmp_out)

        if tmp_out.suffix.lower() not in {".svg", ".png", ".pdf"}:
            raise ValueError(f"Expected output file to have a .svg, .png, or .pdf extension, got {tmp_out.suffix}")

        if not tmp_inp.exists():
            raise FileNotFoundError(tmp_inp)

        if tmp_inp.suffix.lower() not in {".mmd"}:
            raise ValueError(f"Expected input file to have a .mmd extension, got {tmp_inp.suffix}")

        # noinspection SpellCheckingInspection
        command = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{tmp_root}:/data",
            "minlag/mermaid-cli",
            "-t",
            theme,
            "-b",
            background_color,
            "-s",
            str(scale),
            "-w",
            str(width),
            *(() if height is None else ("-H", str(height))),
            "-i",
            tmp_inp.name,
            "-o",
            tmp_out.name,
        ]

        if run(*command).returncode == 0:
            if not tmp_out.exists():
                raise FileNotFoundError(tmp_out)

            shutil.copy(tmp_out, out)
        else:
            raise RuntimeError("Failed to execute mermaid command")


class MermaidExtension(GenImageExtension):
    tags = {"mermaid"}

    def __init__(self, environment: Environment):
        super().__init__(environment)

    @property
    def _valid_keys(self) -> Generator[str]:
        yield from inspect.signature(mermaid).parameters

    @staticmethod
    def modify(**kwargs: Any) -> Generator[tuple[str, Any], None, None]:
        for key, value in kwargs.items():
            if key == "diagram":
                assert "inp" not in kwargs
                yield "inp", value
            else:
                yield key, value

    def callback(
        self,
        inp: Path | str,
        out: Path,
        **kwargs: Any,
    ) -> None:
        if isinstance(inp, str) and inp.endswith(".mmd"):
            inp = Path(inp)

        return mermaid(inp=inp, out=out, **kwargs)
