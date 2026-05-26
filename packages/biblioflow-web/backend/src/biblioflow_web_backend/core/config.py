"""Runtime configuration for biblioflow-web."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str = "biblioflow-web"
    api_prefix: str = "/api"
    data_dir: Path = Path(".biblioflow-web-data")
    static_dir: Path | None = None
    serve_frontend: bool = True
    cors_origins: tuple[str, ...] = ("http://localhost:5173",)

    @classmethod
    def from_env(cls) -> Settings:
        """Create settings from environment variables."""
        data_dir = Path(
            os.environ.get("BIBLIOFLOW_WEB_DATA_DIR") or default_data_dir()
        ).expanduser()
        static_dir_env = os.environ.get("BIBLIOFLOW_WEB_STATIC_DIR")
        cors_origins = tuple(
            origin.strip()
            for origin in os.environ.get(
                "BIBLIOFLOW_WEB_CORS_ORIGINS", "http://localhost:5173"
            ).split(",")
            if origin.strip()
        )
        return cls(
            data_dir=data_dir,
            static_dir=Path(static_dir_env).expanduser() if static_dir_env else None,
            serve_frontend=os.environ.get("BIBLIOFLOW_WEB_SERVE_FRONTEND", "1")
            not in {"0", "false", "False"},
            cors_origins=cors_origins,
        )

    def resolve_static_dir(self) -> Path:
        """Return the directory containing bundled React static assets."""
        if self.static_dir is not None:
            return self.static_dir
        return Path(str(resources.files("biblioflow_web_backend") / "static"))


def default_data_dir() -> Path:
    """Return a safe user-writable default data directory."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "biblioflow-web"
