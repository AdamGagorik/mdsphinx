import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from mdsphinx.logger import run


def mermaid(
    inp: Path | str,
    out: Path,
    theme: str = "default",
    width: int = 800,
    height: int = 600,
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
            "-w",
            str(width),
            "-H",
            str(height),
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
