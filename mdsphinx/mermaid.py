import inspect
import json
import shutil
from collections.abc import Generator
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from typing import cast
from uuid import UUID
from uuid import uuid5

import yaml
from jinja2 import Environment
from jinja2 import nodes
from jinja2 import pass_context
from jinja2.ext import Extension
from jinja2.parser import Parser
from jinja2.runtime import Context
from jinja2.runtime import Macro

from mdsphinx.logger import logger
from mdsphinx.logger import run


namespace = UUID("b5db653c-cc06-466c-9b39-775db782a06f")


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


class MermaidExtension(Extension):
    tags = {"mermaid"}

    def __init__(self, environment: Environment):
        super().__init__(environment)

    def parse(self, parser: Parser) -> nodes.Node:
        line = next(parser.stream).lineno
        block = parser.parse_statements(("name:endmermaid",), drop_needle=True)
        kwargs = yaml.safe_load(cast(nodes.TemplateData, cast(nodes.Output, block[0]).nodes[0]).data)
        callback = self.call_method("_render_mermaid", [nodes.Const(json.dumps(kwargs))])
        return nodes.CallBlock(callback, [], [], block).set_lineno(line)

    @property
    def valid_keys(self) -> Generator[str]:
        excluded = {"context", "output_name_salt", "out"}
        for k in chain(inspect.signature(mermaid).parameters, inspect.signature(self.gen_markdown_lines).parameters):
            if k not in excluded:
                yield k

    @pass_context
    def _render_mermaid(self, context: Context, kwargs_json: str, caller: Macro) -> str:
        kwargs = json.loads(kwargs_json)
        if "diagram" in kwargs:
            kwargs["inp"] = kwargs.get("inp", kwargs.get("diagram", None))
            del kwargs["diagram"]

        unknown_keys = set(kwargs.keys()) - set(self.valid_keys)
        if any(unknown_keys):
            raise TypeError(f"_render_mermaid() got unexpected keyword arguments {''.join(unknown_keys)}")

        return "\n".join(self.gen_markdown_lines(context, output_name_salt=kwargs_json, **kwargs))

    @staticmethod
    def gen_markdown_lines(
        context: Context,
        inp: Path | str,
        ext: str = ".png",
        align: str = "center",
        caption: str | None = None,
        use_cached: bool = True,
        use_myst_syntax: bool = True,
        output_name_salt: str = "...",
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """
        Run mermaid and yield a series of markdown commands to include it .
        """
        ext = "." + ext.lower().lstrip(".")
        if isinstance(inp, str) and inp.endswith(".mmd"):
            Path(inp)

        root = cast(Path, context.parent.get("out_path")).parent
        key = str(uuid5(namespace, str(inp) + output_name_salt))
        out = root.joinpath(key).with_suffix(ext)

        if not out.exists() or not use_cached:
            mermaid(inp=inp, out=out, **kwargs)
        else:
            logger.warn(dict(action="use-cached", out=out))

        if use_myst_syntax:
            if caption is not None:
                yield f":::{{figure}} {out.name}"
            else:
                yield f":::{{image}} {out.name}"
            if kwargs.get("width", None) is not None:
                yield f":width: {kwargs['width']}px"
            if kwargs.get("height", None) is not None:
                yield f":height: {kwargs['height']}px"
            if align is not None:
                yield f":align: {align}"
            if caption is not None:
                yield f":\n{caption}"
            yield r":::"
        else:
            if caption is not None:
                yield f"![{caption}]({out.name})"
            else:
                yield f"![{out.name}]"
