# biblioflow-web backend

FastAPI backend for the `biblioflow-web` application.

This directory is an individual Python package published as `biblioflow-web`. It
serves `/api/*` routes and, in production, serves the built React frontend from
`src/biblioflow_web_backend/static/`.

## Development

```bash
cd packages/biblioflow-web/backend
poetry install --extras dev
PYTHONPATH=src:../../biblioflow/src poetry run pytest \
  --cov=biblioflow_web_backend --cov-fail-under=90
poetry run uvicorn biblioflow_web_backend.main:app --reload --port 0
```

Use `--port 0` to bind a random free port, or pass a fixed port such as
`--port 8000` when the frontend development proxy needs a stable backend URL.

Set `BIBLIOFLOW_WEB_DATA_DIR` to control where projects, uploads, datasets,
exports, and caches are written. Runtime data is never written into the
installed Python package directory.

## PubMed/PMC screening imports

The backend exposes staged PubMed and PubMed Central search endpoints. The
recommended workflow is:

1. `POST /api/projects/{project_id}/sources/search` to call the core
   `biblioflow` API connectors and persist results as screening candidates.
2. `PATCH /api/projects/{project_id}/sources/searches/{search_id}/candidates` to
   mark candidates as selected, excluded, duplicate, or candidate.
3. `POST /api/projects/{project_id}/sources/searches/{search_id}/promote` to
   create a regular active dataset from selected candidate IDs or statuses.

The older direct `POST /api/projects/{project_id}/sources/import` route remains
available for compatibility when an intermediate screening step is not needed.

Configure NCBI contact details with environment variables when desired:

```bash
export BIBLIOFLOW_NCBI_EMAIL="researcher@example.org"
export BIBLIOFLOW_NCBI_API_KEY="optional-key"
```

Submitted API keys are passed to `biblioflow` for the request only; they are not
persisted in project metadata, remote-search payloads, datasets, or returned by
the API.

## Bundling the frontend

The React source lives in `../frontend`. For release builds, build the frontend
and copy its `dist/` output into the backend static package data:

```bash
cd packages/biblioflow-web/backend
python scripts/build_frontend.py
poetry build
```

Users installing the built `biblioflow-web` wheel or sdist do not need Node/npm.
