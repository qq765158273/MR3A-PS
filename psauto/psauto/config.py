"""Load the local JumpServer connection configuration."""

from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class Config:
    jumpserver_url: str
    connect_url: str = ""
    display_selector: str = ""
    display_frame: str | None = None
    pre_connect_clicks: list[str] = field(default_factory=list)
    viewport_width: int = 1600
    viewport_height: int = 900
    headless: bool = True
    browser_channel: str | None = None
    ignore_https_errors: bool = False
    storage_state: str = "state/storage.json"
    resource_dir: str = "resource"
    base_dir: Path = field(default_factory=Path.cwd, init=False, repr=False)

    def resolve_path(self, path: str | Path) -> Path:
        path = Path(path)
        return path if path.is_absolute() else self.base_dir / path


def load_config(path: str | Path = "config.json") -> Config:
    path = Path(path).resolve()
    with path.open(encoding="utf-8") as config_file:
        config = Config(**json.load(config_file))
    config.base_dir = path.parent
    return config
