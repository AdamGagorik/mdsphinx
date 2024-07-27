import os
import shlex
from datetime import datetime
from datetime import UTC
from pathlib import Path
from tempfile import gettempdir

NOW = datetime.now(UTC)
TMP_ROOT = Path(gettempdir())
MDSPHINX_ROOT = Path(__file__).parent
TEMPLATE_ROOT = MDSPHINX_ROOT / "templates"

CONFIG_ROOT: Path = Path(os.environ.get("MDSPHINX_CONFIG_ROOT", default=Path.home() / ".config" / "mdsphinx"))
if CONFIG_ROOT.exists():
    assert CONFIG_ROOT.is_dir(), "Configuration root is not a directory."

CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
assert CONFIG_ROOT != Path.home(), "Configuration root is the home directory."

ENVIRONMENTS: Path = CONFIG_ROOT / "environments"
ENVIRONMENTS.mkdir(parents=True, exist_ok=True)

ENVIRONMENTS_REGISTRY: Path = CONFIG_ROOT / "registry"

DEFAULT_ENVIRONMENT: str = "default"
DEFAULT_ENVIRONMENT_PACKAGES: tuple[str, ...] = (
    "furo",
    "nbsphinx",
    "myst-parser",
    "sphinx-copybutton",
    "sphinxcontrib-confluencebuilder",
)

LATEX_COMMAND: tuple[tuple[str, ...], ...] = tuple(
    tuple(shlex.split(command)) for command in os.environ.get("MDSPHINX_LATEX_COMMAND", "tectonic '{tex}'").split(";")
)
