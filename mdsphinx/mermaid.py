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


@pass_context
def gen_markdown_lines(
    context: Context,
    salt: str,
    inp: Path | str,
    ext: str = ".png",
    use_cached: bool = True,
    use_myst_syntax: bool = True,
    align: str = "center",
    caption: str | None = None,
    **kwargs: Any,
) -> Generator[str, None, None]:
    """
    Run mermaid and yield a series of markdown commands to include it .
    """
    ext = "." + ext.lower().lstrip(".")
    if isinstance(inp, str) and inp.endswith(".mmd"):
        inp = Path(inp)

    root = cast(Path, context.parent.get("out_path")).parent
    key = str(uuid5(namespace, str(inp) + salt))
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


class MermaidExtension(Extension):
    tags = {"mermaid"}

    def __init__(self, environment: Environment):
        super().__init__(environment)

    def parse(self, parser: Parser) -> nodes.Node:
        lineno = next(parser.stream).lineno
        kwargs = dict(parse_block_kwargs(parser, valid_keys=set(self.valid_keys)))

        body = parser.parse_statements(("name:endmermaid",), drop_needle=True)
        kwargs["inp"] = cast(nodes.TemplateData, cast(nodes.Output, body[0]).nodes[0]).data

        call = self.call_method("_render_mermaid", [nodes.Const(json.dumps(kwargs))])
        return nodes.CallBlock(call, [], [], body).set_lineno(lineno)

    @property
    def valid_keys(self) -> Generator[str]:
        excluded = {"context", "salt", "inp", "out"}
        for k in chain(inspect.signature(mermaid).parameters, inspect.signature(gen_markdown_lines).parameters):
            if k not in excluded:
                yield k

    @pass_context
    def _render_mermaid(self, context: Context, kwargs_json: str, caller: Macro) -> str:
        kwargs = json.loads(kwargs_json)
        return "\n".join(gen_markdown_lines(context, salt=kwargs_json, **kwargs))


def parse_block_kwargs(parser: Parser, valid_keys: set[str]) -> Generator[tuple[str, str], None, None]:
    """
    Parse a jinja2 token stream for keyword arguments.
    """
    num_kwargs = 0
    while not parser.stream.current.type == "block_end":
        if num_kwargs >= len(valid_keys):
            raise RuntimeError(f"Expected at most {len(valid_keys)} arguments, got {num_kwargs}")

        if parser.stream.current.type == "name":
            key = parser.stream.current.value
            if key not in valid_keys:
                raise KeyError(key)

            next(parser.stream)
            parser.stream.expect("assign")
            expr = parser.parse_expression()

            if isinstance(expr, nodes.Const):
                yield key, expr.value
                num_kwargs += 1
            else:
                raise RuntimeError(f"Expected constant, got {expr}")
        else:
            raise RuntimeError(f"Expected name, got {parser.stream.current.type}")

        if parser.stream.current.type == "block_end":
            break
        else:
            parser.stream.expect("comma")
