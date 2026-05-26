# biblioflow-web backend

FastAPI backend for the `biblioflow-web` application.

This directory is an individual Python package published as `biblioflow-web`.
It serves `/api/*` routes and, in production, serves the built React frontend
from `src/biblioflow_web_backend/static/`.

## Development

```bash
cd packages/biblioflow-web/backend
poetry install --extras dev
PYTHONPATH=../../biblioflow/src poetry run pytest
poetry run uvicorn biblioflow_web_backend.main:app --reload
```

Set `BIBLIOFLOW_WEB_DATA_DIR` to control where projects, uploads, datasets,
exports, and caches are written. Runtime data is never written into the
installed Python package directory.

## Bundling the frontend

The React source lives in `../frontend`. For release builds, build the frontend
and copy its `dist/` output into the backend static package data:

```bash
cd packages/biblioflow-web/backend
python scripts/build_frontend.py
poetry build
```

Users installing the built `biblioflow-web` wheel or sdist do not need Node/npm.
