# biblioflow-web frontend

Private React/Vite frontend for `biblioflow-web`.

This package is not published to npm. It is built during the `biblioflow-web`
release process, and the generated `dist/` files are copied into the backend
Python package under `src/biblioflow_web_backend/static/`.

## Development

```bash
cd packages/biblioflow-web/frontend
npm install
npm run dev
```

By default, the app calls `/api`. In local development, configure Vite proxying
or set `VITE_BIBLIOFLOW_WEB_API_BASE_URL`.

## Production build

```bash
npm run build
```

The build output is written to `dist/` and consumed by the backend package
build.
