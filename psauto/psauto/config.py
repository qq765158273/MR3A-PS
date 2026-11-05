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
    connection_mode: str = "launch"
    cli_session: str = "psauto-discovery"
    cli_script: str = "../.psauto-runtime/node_modules/@playwright/cli/playwright-cli.js"
    cli_workdir: str = "../.psauto-runtime"
    cli_persistent_client: bool = True
    cli_settle_ms: int | None = None
    capture_mode: str = "viewport"
    canvas_refresh_mode: str = "guacamole"
    text_input_mode: str = "keyboard"
    remote_width: int = 1920
    remote_height: int = 1080
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
