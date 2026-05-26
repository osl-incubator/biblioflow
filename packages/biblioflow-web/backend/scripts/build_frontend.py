"""Build and copy the React frontend into backend static package data."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = ROOT / "biblioflow-web" / "frontend"
BACKEND_STATIC_DIR = (
    ROOT / "biblioflow-web" / "backend" / "src" / "biblioflow_web_backend" / "static"
)


def run(command: list[str], *, cwd: Path) -> None:
    """Run a subprocess command."""
    subprocess.run(command, cwd=cwd, check=True)


def clean_static() -> None:
    """Remove generated static assets while preserving the directory."""
    BACKEND_STATIC_DIR.mkdir(parents=True, exist_ok=True)
    for path in BACKEND_STATIC_DIR.iterdir():
        if path.name == ".gitkeep":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def copy_dist() -> None:
    """Copy frontend dist files into backend static package data."""
    dist_dir = FRONTEND_DIR / "dist"
    if not (dist_dir / "index.html").exists():
        msg = f"Frontend build output is missing: {dist_dir / 'index.html'}"
        raise SystemExit(msg)
    clean_static()
    for source in dist_dir.iterdir():
        target = BACKEND_STATIC_DIR / source.name
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()

    if not args.skip_install:
        install_command = (
            ["npm", "ci"]
            if (FRONTEND_DIR / "package-lock.json").exists()
            else ["npm", "install"]
        )
        run(install_command, cwd=FRONTEND_DIR)
    if not args.skip_build:
        run(["npm", "run", "build"], cwd=FRONTEND_DIR)
    copy_dist()


if __name__ == "__main__":
    main()
