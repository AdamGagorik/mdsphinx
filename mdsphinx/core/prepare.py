from __future__ import annotations

import dataclasses
import functools
import shutil
import textwrap
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterable
from pathlib import Path
from string import ascii_uppercase
from typing import Annotated
from typing import Any
from typing import cast
from typing import ClassVar

import networkx as nx
from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import StrictUndefined
from jinja2_mermaid_extension import MermaidExtension
from jinja2_mermaid_extension import TikZExtension
from natsort import os_sorted
from typer import Option

from mdsphinx.config import DEFAULT_ENVIRONMENT
from mdsphinx.config import NOW
from mdsphinx.config import TMP_ROOT
from mdsphinx.core.environment import VirtualEnvironment
from mdsphinx.core.quickstart import sphinx_quickstart
from mdsphinx.logger import logger
from mdsphinx.tempdir import get_out_root
from mdsphinx.types import OptionalPath


EPILOG = ""


def prepare(
    inp: Annotated[Path, "The input path or directory with markdown files."],
    context: Annotated[OptionalPath, Option(help="JSON/YAML variables to inject when rendering")] = None,
    env_name: Annotated[str, Option(help="The environment name.")] = DEFAULT_ENVIRONMENT,
    tmp_root: Annotated[Path, Option(help="The directory for temporary output.")] = TMP_ROOT,
    overwrite: Annotated[bool, Option(help="Force creation of new output folder in --tmp-root?")] = False,
    reconfigure: Annotated[bool, Option(help="Remove existing sphinx conf.py file?")] = False,
) -> None:
    """
    Preprocess the input files.
    """
    inp = inp.resolve()
    tmp_root = tmp_root.resolve()
    out_root = get_out_root(inp.name, root=tmp_root)

    if not inp.exists():
        raise FileNotFoundError(inp)

    venv = VirtualEnvironment.from_db(env_name)
    sphinx_quickstart(inp, out_root, venv, remove=reconfigure)

    if context is None:
        for root in (inp.parent, Path.cwd()):
            for base in ("context.yml", "context.yaml"):
                path = root / base
                if path.exists():
                    context = path
                    break

    renderer = Renderer.create(
        context=context,
        inp_path=inp if inp.is_file() else None,
        inp_root=inp if inp.is_dir() else inp.parent,
        out_root=get_out_root(inp.name, root=tmp_root, overwrite=overwrite),
    )

    renderer.render()
    renderer.create_index()

    if not renderer.index.exists():
        raise FileNotFoundError(renderer.index)


@functools.lru_cache(maxsize=1)
def env() -> Environment:
    instance = Environment(
        loader=PackageLoader("mdsphinx", "templates"), undefined=StrictUndefined, extensions=[MermaidExtension, TikZExtension]
    )
    instance.globals["indent"] = indent
    instance.globals["titleize"] = titleize
    return instance


C_LUT = ("#", "*", "=", "-", "^", "`", '"') + tuple(ascii_uppercase)


def indent(s: str, width: int) -> str:
    return textwrap.indent(str(s).strip(), width * " ")


def titleize(s: str, c: str | int = 0, exclude_if: bool = False) -> str:
    if exclude_if:
        return ""

    c = c if isinstance(c, str) else C_LUT[c % len(C_LUT)]
    return f"{c * len(s.strip())}\n{s.strip()}\n{c * len(s.strip())}"


@dataclasses.dataclass(frozen=True)
class Renderer:
    inp_root: Path
    out_root: Path
    inp_path: Path | None = None
    context: dict[str, Any] = dataclasses.field(default_factory=dict)

    SOURCES: ClassVar[frozenset[str]] = frozenset({".md", ".markdown", ".rst", ".txt"})
    RESOURCES: ClassVar[frozenset[str]] = frozenset({".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".html", ".ipynb", ".mmd", ".tex"})
    EXCLUDED_NAMES: ClassVar[frozenset[str]] = frozenset(
        {".git", ".github", ".vscode", "__pycache__", ".venv", "venv", ".idea", "_static", "_templates"}
    )

    @property
    def index(self) -> Path:
        path = self.out_root.joinpath("source", "index.md")
        return path if path.exists() else path.with_suffix(".rst")

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

    def create_index(self) -> None:
        if any(
            [
                self.inp_path is not None and self.inp_path.is_file() and self.inp_path.name == "index",
                self.inp_root is not None and self.inp_root.is_dir() and self.inp_root.joinpath("index.md").exists(),
                self.inp_root is not None and self.inp_root.is_dir() and self.inp_root.joinpath("index.rst").exists(),
            ]
        ):
            return

        graph = self._make_source_graph(self.index.parent)
        for node, data in graph.nodes(data=True):
            if data["type"] == "D":
                rendered = (
                    env()
                    .get_template("index.rst.jinja")
                    .render(
                        title=data["title"],
                        depth=data["depth"],
                        documents=os_sorted(self._get_documents(graph, node), key=lambda x: x[0]),
                    )
                )
                index = data["path"].joinpath("index.rst")
                logger.info("generate: %s", index)
                with index.open("w") as stream:
                    stream.write(rendered)

    @staticmethod
    def _get_documents(graph: nx.DiGraph, top_node: Path) -> Any:
        for fp in cast(Callable[[Any], Iterable[Any]], graph.successors)(top_node):
            d = graph.nodes[fp]
            if d["type"] == "S":
                yield fp, d
            elif d["type"] == "D":
                yield fp.joinpath("index.rst"), d

    def _make_source_graph(self, top: Path) -> nx.DiGraph:  # noqa: C901
        graph = nx.DiGraph()

        for root, dir_names, file_names in top.walk(top_down=True):
            # get depth
            depth = len(root.relative_to(top).parts)

            # ensure root node
            if root not in graph:
                title = str(self.inp_root.name)
                graph.add_node(root, type="D", path=root, depth=depth, title=title, target=root.with_suffix(""))

            # add valid dir nodes
            dir_names[:] = [d for d in dir_names if d not in self.EXCLUDED_NAMES]
            for base in dir_names:
                path = root / base
                if path not in graph:
                    graph.add_node(
                        path,
                        type="D",
                        path=path,
                        depth=depth + 1,
                        title=path.name,
                        target=path.joinpath("index").relative_to(root),
                    )
                    graph.add_edge(root, path)

            # add valid source nodes
            for base in file_names:
                if base in {"index.md", "index.rst"}:
                    continue

                path = root / base
                if path.suffix.lower() in self.SOURCES:
                    graph.add_node(
                        path,
                        type="S",
                        path=path,
                        depth=depth + 1,
                        title=path.with_suffix("").name,
                        target=path.relative_to(root).with_suffix(""),
                    )
                    graph.add_edge(root, path)

        # prune directory with zero content
        to_remove = set()
        for node, data in graph.nodes(data=True):
            if data["type"] == "D":
                if not any(
                    graph.nodes[n]["type"] == "S" for n in cast(Callable[[Any, Any], Iterable[Any]], nx.descendants)(graph, node)
                ):
                    to_remove.add(node)

        graph.remove_nodes_from(to_remove)

        return graph

    @classmethod
    def _get_index_paths(cls, top: Path, recursive: bool = False) -> Generator[Path]:
        for root, dir_names, file_names in top.walk(top_down=True):

            for base in file_names:
                if base in {"index.md", "index.rst"}:
                    continue

                path = root / base
                if path.suffix in cls.SOURCES:
                    yield path

            if not recursive:
                dir_names.clear()

            dir_names[:] = [d for d in dir_names if d not in cls.EXCLUDED_NAMES]

    def __post_init__(self) -> None:
        self.context.update(date=NOW.date(), time=NOW.time())

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
        logger.info(f"creating: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if render:
            template = env().from_string(content)
            rendered = template.render(
                **self.context,
                source=None,
                tikz_input_root=None,
                tikz_output_root=out_path.parent,
                mermaid_input_root=None,
                mermaid_output_root=out_path.parent,
            )
        else:
            rendered = content

        with out_path.open("w") as stream:
            stream.write(rendered)

    def _render_source(self, source: Path) -> None:
        out_path = self.out_root.joinpath("source") / source.relative_to(self.inp_root)
        logger.info(f"rendered: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        with source.open("r") as stream:
            template = env().from_string(stream.read())
            rendered = template.render(
                **self.context,
                source=source,
                tikz_input_root=source.parent,
                tikz_output_root=out_path.parent,
                mermaid_input_root=source.parent,
                mermaid_output_root=out_path.parent,
            )

        with out_path.open("w") as stream:
            stream.write(rendered)

    def _render_resource(self, resource: Path) -> None:
        out_path = self.out_root.joinpath("source") / resource.relative_to(self.inp_root)
        logger.info(f"mirror: {out_path}")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(resource, out_path)
