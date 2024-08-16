import inspect
import json
from collections.abc import Generator
from pathlib import Path
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

namespace = UUID("b5db653c-cc06-466c-9b39-775db782a06f")


class GenImageExtension(Extension):
    tags = {"yaml"}

    def __init__(self, environment: Environment):
        super().__init__(environment)

    def parse(self, parser: Parser) -> nodes.Node:
        line = next(parser.stream).lineno
        block = parser.parse_statements((f"name:end{next(iter(self.tags))}",), drop_needle=True)
        kwargs = yaml.safe_load(cast(nodes.TemplateData, cast(nodes.Output, block[0]).nodes[0]).data)
        callback = self.call_method("_render", [nodes.Const(json.dumps(kwargs))])
        return nodes.CallBlock(callback, [], [], block).set_lineno(line)

    @staticmethod
    def modify(**kwargs: Any) -> Generator[tuple[str, Any], None, None]:
        yield from kwargs.items()

    def callback(self, inp: Path | str, out: Path, **kwargs: Any) -> None:
        raise NotImplementedError

    @property
    def _valid_keys(self) -> Generator[str]:
        yield from ()

    @pass_context
    def _render(self, context: Context, kwargs_json: str, caller: Macro) -> str:
        kwargs = dict(self.modify(**json.loads(kwargs_json)))
        valid_keys = set(inspect.signature(self._gen_markdown_lines).parameters) | set(self._valid_keys)
        valid_keys = valid_keys - {"context", "output_name_salt", "out"}
        unknown_keys = set(kwargs.keys()) - valid_keys
        if any(unknown_keys):
            raise TypeError(f"callback got unexpected keyword arguments: {', '.join(unknown_keys)}")

        return "\n".join(self._gen_markdown_lines(context, output_name_salt=kwargs_json, **kwargs))

    def _gen_markdown_lines(
        self,
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
        Run callback and yield a series of markdown commands to include it .
        """
        root = cast(Path, context.parent.get("out_path")).parent
        key = str(uuid5(namespace, str(inp) + output_name_salt))
        out = root.joinpath(key).with_suffix("." + ext.lower().lstrip("."))

        if not out.exists() or not use_cached:
            self.callback(inp=inp, out=out, **kwargs)
        else:
            logger.warn("existing: %s", out)

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
