"""Command-line entry point for serving biblioflow-web."""

from __future__ import annotations


def main() -> None:
    """Run the biblioflow-web ASGI application with uvicorn."""
    import uvicorn

    uvicorn.run("biblioflow_web_backend.main:app", host="127.0.0.1", port=8000)
