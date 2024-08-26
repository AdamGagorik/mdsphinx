from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from mdsphinx.config import TEMPLATE_ROOT
from mdsphinx.core.environment import VirtualEnvironment


def master_doc(inp_path: Path) -> Generator[str]:
    if inp_path.is_file() and inp_path.with_suffix("").name == "index":
        yield from ("--master", "index", "--suffix", inp_path.suffix)

    for suffix in (".md", ".rst"):
        path = inp_path.joinpath("index").with_suffix(suffix)
        if path.exists():
            yield from ("--master", "index", "--suffix", path.suffix)


def get_html_theme(venv: VirtualEnvironment) -> str | None:
    if venv.has_package("furo"):
        return "furo"
    else:
        return None


def get_extra_extensions(venv: VirtualEnvironment) -> Generator[str]:
    if venv.has_package("myst_parser"):
        yield "myst_parser"
    if venv.has_package("sphinxcontrib-confluencebuilder"):
        yield "sphinxcontrib.confluencebuilder"


LATEX_MAIN_TEMPLATE: str = "latex.tex.jinja"
SPHINX_CFG_TEMPLATE: str = "conf.py.jinja"


def get_main_sphinx_config() -> Path | None:
    if (path := TEMPLATE_ROOT.joinpath(SPHINX_CFG_TEMPLATE)).exists():
        return path
    else:
        return None


def get_base_sphinx_config(venv: VirtualEnvironment) -> Path | None:
    for path in venv.path.glob("lib/python*/site-packages/sphinx/templates/quickstart/conf.py.jinja"):
        return path
    else:
        return None


def get_custom_templatedir(inp_path: Path) -> Path | None:
    for root in (inp_path.parent, Path.cwd(), TEMPLATE_ROOT):
        for base in (SPHINX_CFG_TEMPLATE, LATEX_MAIN_TEMPLATE):
            path = root.joinpath(base)
            if path.exists():
                return path.parent
    return None


def sphinx_quickstart(
    inp_path: Path, out_root: Path, venv: VirtualEnvironment, remove: bool = False, html_theme: str | None = None
) -> None:
    sphinx_config_path = out_root.joinpath("source", "conf.py")

    if sphinx_config_path.exists() and remove:
        sphinx_config_path.unlink()

    if not sphinx_config_path.exists():
        html_theme = html_theme if html_theme is not None else get_html_theme(venv)
        extra_extensions = ",".join(get_extra_extensions(venv))
        custom_templatedir = get_custom_templatedir(inp_path)
        base_sphinx_config = get_base_sphinx_config(venv)
        main_sphinx_config = get_main_sphinx_config()

        venv.run(
            "sphinx-quickstart",
            *("-p", "mdsphinx"),
            *("-a", "mdsphinx"),
            *("-v", "1.0.0"),
            "--no-batchfile",
            "--no-makefile",
            "--ext-mathjax",
            *(() if not extra_extensions else ("--extensions", extra_extensions)),
            *(() if not custom_templatedir else ("--templatedir", str(custom_templatedir))),
            *(() if not base_sphinx_config else ("-d", f"base_sphinx_config={base_sphinx_config}")),
            *(() if not main_sphinx_config else ("-d", f"main_sphinx_config={main_sphinx_config}")),
            *(() if not html_theme else ("-d", f"html_theme={html_theme}")),
            *("-d", f"inp_path_name={inp_path.with_suffix('').name}"),
            "--sep",
            "-q",
            *master_doc(inp_path),
            str(out_root),
        )
