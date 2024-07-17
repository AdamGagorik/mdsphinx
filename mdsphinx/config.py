import os
from datetime import datetime
from datetime import UTC
from pathlib import Path

NOW = datetime.now(UTC)

CONFIG_ROOT: Path = Path(os.environ.get("MDSPHINX_CONFIG_ROOT", default=Path.home() / ".config" / "mdsphinx"))
if CONFIG_ROOT.exists():
    assert CONFIG_ROOT.is_dir(), "Configuration root is not a directory."

CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
assert CONFIG_ROOT != Path.home(), "Configuration root is the home directory."

ENVIRONMENTS: Path = CONFIG_ROOT / "environments"
ENVIRONMENTS.mkdir(parents=True, exist_ok=True)

ENVIRONMENTS_REGISTRY: Path = CONFIG_ROOT / "registry"

DEFAULT_ENVIRONMENT: str = "default"
DEFAULT_ENVIRONMENT_PACKAGES: tuple[str, ...] = ("myst-parser", "nbsphinx", "furo", "sphinx-copybutton")
