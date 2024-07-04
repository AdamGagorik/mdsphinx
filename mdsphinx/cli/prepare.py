from __future__ import annotations

import dataclasses
import functools
import shutil
from pathlib import Path
from typing import Annotated
from typing import Any
from typing import ClassVar
from typing import Optional

from jinja2 import Environment
from jinja2 import StrictUndefined
from typer import Option

from mdsphinx.config import DT
from mdsphinx.logger import logger
from mdsphinx.tempdir import get_out_root
from mdsphinx.tempdir import TMP_ROOT


OptionalPath = Optional[Path]


def prepare(
    inp: Annotated[Path, "The input path or directory with markdown files."],
    context: Annotated[OptionalPath, Option(help="JSON/YAML variables to inject when rendering")] = None,
    tmp_root: Annotated[Path, Option(help="The directory for temporary output.")] = TMP_ROOT,
    overwrite: Annotated[bool, Option(help="Force creation of new output folder in --tmp-root?")] = False,
) -> None:
    """
    Preprocess the input files.
    """
    inp = inp.resolve()
    tmp_root = tmp_root.resolve()

    if not inp.exists():
        raise FileNotFoundError(inp)

    Renderer.create(
        context=context,
        inp_path=inp if inp.is_file() else None,
        inp_root=inp if inp.is_dir() else inp.parent,
        out_root=get_out_root(inp.name, root=tmp_root, overwrite=overwrite),
    ).render()


@functools.lru_cache(maxsize=1)
def env() -> Environment:
    return Environment(undefined=StrictUndefined)


@dataclasses.dataclass(frozen=True)
class Renderer:
    inp_root: Path
    out_root: Path
    inp_path: Path | None = None
    context: dict[str, Any] = dataclasses.field(default_factory=dict)

    SOURCES: ClassVar[frozenset[str]] = frozenset({".md", ".markdown", ".rst", ".txt"})
    RESOURCES: ClassVar[frozenset[str]] = frozenset({".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf"})
    EXCLUDED_NAMES: ClassVar[frozenset[str]] = frozenset({".git", ".github", ".vscode", "__pycache__", ".venv", "venv", ".idea"})

    def render(self) -> None:
        logger.info("inp_path: %s", self.inp_path)
        logger.info("inp_root: %s", self.inp_root)
        logger.info("out_root: %s", self.out_root)

        self.out_root.mkdir(parents=True, exist_ok=True)
        self._render_content(".gitignore", "*\n", render=False)

        for root, d_bases, f_bases in self.inp_root.walk():
            if root.name.startswith(".") or root.name in self.EXCLUDED_NAMES or root == self.out_root:
                d_bases[:] = []
                continue

            for base in f_bases:
                path = root / base

                if path.suffix.lower() in self.SOURCES:
                    if self.inp_path is not None and path != self.inp_path:
                        continue

                    self._render_source(path)

                elif path.suffix in self.RESOURCES:
                    self._render_resource(path)

            if self.inp_path is not None:
                break

    def __post_init__(self) -> None:
        self.context.update(date=DT.date(), time=DT.time())

    @classmethod
    def create(cls, context: str | Path | dict[str, Any] | None, **kwargs: Any) -> Renderer:
        return cls(context=cls._load_context(context), **kwargs)

    @classmethod
    def _load_context(cls, context: str | Path | dict[str, Any] | None) -> dict[str, Any]:
        if isinstance(context, dict):
            return context

        if isinstance(context, str):
            raise NotImplementedError

        if context is None:
            return {}

        match context.suffix.lower():
            case ".json":
                import json

                with context.open("r") as stream:
                    data: dict[str, Any] = json.load(stream)
                    return {} if not isinstance(data, dict) else data
            case ".yaml" | ".yml":
                import yaml

                with context.open("r") as stream:
                    data = yaml.load(stream, Loader=yaml.FullLoader)
                    return {} if not isinstance(data, dict) else data
            case _:
                raise ValueError(f"Can not load context from {context}")

    def _render_content(self, stem: Path | str, content: str, render: bool = False) -> None:
        out_path = self.out_root / stem

        if render:
            template = env().from_string(content)
            rendered = template.render(**self.context)
        else:
            rendered = content

        logger.info(f"create: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as stream:
            stream.write(rendered)

    def _render_source(self, source: Path) -> None:
        out_path = self.out_root / source.relative_to(self.inp_root)

        with source.open("r") as stream:
            template = env().from_string(stream.read())
            rendered = template.render(**self.context)

        logger.info(f"render: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as stream:
            stream.write(rendered)

    def _render_resource(self, resource: Path) -> None:
        out_path = self.out_root / resource.relative_to(self.inp_root)
        logger.info(f"mirror: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(resource, out_path)
