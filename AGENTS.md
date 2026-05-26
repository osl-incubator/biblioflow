# biblioflow Contributor Guide

This file is the shared operating manual for AI contributors working in
`biblioflow`.

## Project identity

- PyPI package: `biblioflow`
- Python import package: `biblioflow`
- Recommended import alias: `bf`
- CLI command: `biblioflow`
- Repository: `osl-incubator/biblioflow`
- Build backend: Poetry
- Environment/workflow: conda + Poetry + Makim
- Runtime: Python 3.10+

Use `biblioflow` everywhere. Do not introduce a hyphenated package, import,
command, documentation alias, or compatibility shim.

## Project scope

`biblioflow` is a Python-native bibliographic metadata and bibliometrics
workflow toolkit inspired by the R bibliometrics ecosystem, especially the R
package `bibliometrix`. It should provide Pythonic ingestion, normalization,
descriptive analysis, matrix/network construction, science mapping, thematic
analysis, and export workflows.

The package should not be a direct translation of `bibliometrix` function names.
Prefer Pythonic public APIs such as:

```python
import biblioflow as bf

records = bf.load(...)
summary = bf.analyze(records)
net = bf.network(records, ...)
themes = bf.map_themes(records, ...)
evolution = bf.trace_themes(records, ...)
```

## Design constraints

1. Keep the base install lightweight.
2. Treat bibliographic records as structured metadata, not as arbitrary ad hoc
   tables.
3. Preserve raw source records where practical for traceability.
4. Distinguish source format (`ris`, `bibtex`, `csv`, `xml`, `json`, `nbib`,
   `tsv`) from semantic provider (`scopus`, `wos`, `pubmed`, `pmc`, `openalex`,
   `crossref`, `lens`, `dimensions`, `cochrane`, `generic`).
5. Validate bibliographic data and analysis assumptions with structured reports
   and warnings.
6. Keep API connectors optional where they bring substantial extra dependency
   weight or credentials.
7. Do not add required dependencies on Graphviz, Node, Mermaid CLI, browser
   engines, Playwright, Selenium, Matplotlib, Plotly, or other heavy rendering
   stacks for core bibliometric workflows.

Preferred parser/connector direction from the project plan:

- RIS: `rispy`
- PubMed and PubMed Central: `pymedx`, maintained by OSL Incubator

## Repository layout

The repository is organized as a monorepo. The `biblioflow` package lives under `packages/biblioflow`:

- `packages/biblioflow/src/biblioflow/`: Python package
- `packages/biblioflow/src/biblioflow/core/`: dataset, schema, warnings, exceptions, typing
- `packages/biblioflow/src/biblioflow/load/`: dispatcher, inference, registry, load results
- `packages/biblioflow/src/biblioflow/io/`: format readers/writers
- `packages/biblioflow/src/biblioflow/providers/`: source-specific normalization
- `packages/biblioflow/src/biblioflow/connectors/`: optional API connector adapters
- `packages/biblioflow/src/biblioflow/normalize/`: field, author, affiliation, keyword, reference,
  identifier, and deduplication helpers
- `packages/biblioflow/src/biblioflow/analysis/`: descriptive bibliometric indicators
- `packages/biblioflow/src/biblioflow/matrices/`: incidence, co-occurrence, collaboration,
  co-citation, coupling, and citation matrices
- `packages/biblioflow/src/biblioflow/networks/`: graph construction, metrics, clustering, export
- `packages/biblioflow/src/biblioflow/mapping/`: thematic maps, thematic evolution, conceptual
  structure, historiography
- `packages/biblioflow/src/biblioflow/export/`: tabular and network exports
- `packages/biblioflow/src/biblioflow/compat/`: optional Bibliometrix-style compatibility helpers
- `packages/biblioflow/examples/`: runnable example inputs/scripts
- `packages/biblioflow/tests/`: pytest coverage
- `packages/biblioflow-web/backend/`: FastAPI package published as `biblioflow-web`
- `packages/biblioflow-web/backend/src/biblioflow_web_backend/static/`: built
  React assets copied in during package/release builds
- `packages/biblioflow-web/frontend/`: private React/Vite source app, not
  published to npm
- `packages/biblioflow-nb/`: Jupyter/Colab widget application published as
  `biblioflow-nb`
- `packages/biblioflow-nb/src/biblioflow_nb/`: notebook app package
- `docs/`: Quarto documentation website

## Development commands

```bash
conda env create -f conda/dev.yaml
conda activate biblioflow
cd packages/biblioflow
poetry config virtualenvs.create false
poetry install --extras "dev yaml"
```

From the repository root, use the Makim workflow:

```bash
makim tests.linter
makim tests.unit
makim package.build
makim docs.build
makim all.ci
```

Web package workflow:

```bash
makim web.backend.tests
makim web.frontend.install
makim web.frontend.build
makim web.package.build
```

Notebook app workflow:

```bash
makim nb.tests
makim nb.package.build
makim nb.examples.check
```

Keep reusable bibliometric logic in `packages/biblioflow`. The
`biblioflow-web` backend should orchestrate HTTP/session/storage/static-serving
concerns, the frontend should render API responses, and `biblioflow-nb` should
only orchestrate notebook widgets and call `biblioflow` APIs.

## Implementation rules

1. Keep README examples, docs, and examples in sync with public API changes.
2. Add tests for model, validation, normalization, ingestion, analysis, network,
   IO, export, and CLI changes.
3. Preserve a Pythonic main namespace; put Bibliometrix compatibility aliases in
   `biblioflow.compat` only.
4. Do not introduce hyphenated aliases for the package, import, or CLI.
5. When the project plan and current scaffold differ, prefer the project plan for
   naming and architecture, but do not invent full implementation code unless
   explicitly requested.
