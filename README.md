# biblioflow

![CI](https://img.shields.io/github/actions/workflow/status/osl-incubator/biblioflow/ci.yml?logo=github&label=CI)
[![Python Versions](https://img.shields.io/pypi/pyversions/biblioflow)](https://pypi.org/project/biblioflow/)
[![Package Version](https://img.shields.io/pypi/v/biblioflow?color=blue)](https://pypi.org/project/biblioflow/)
![License](https://img.shields.io/pypi/l/biblioflow?color=blue)

`biblioflow` is a Python-native toolkit for bibliographic metadata,
bibliometrics, science mapping, and literature-review data workflows. The
project is inspired by the R bibliometrics ecosystem, especially
[`bibliometrix`](https://www.bibliometrix.org/), while aiming for a Pythonic API
and dataframe-centric workflows.

This repository currently includes an implementation of the core workflow
described in the project plan, including ingestion, normalization, validation,
descriptive analysis, matrices, networks, compatibility helpers, and exports.
Advanced provider connectors and clustering methods will continue to evolve.

## Current and planned scope

- File-based ingestion for RIS, BibTeX, CSV/TSV, JSON/JSONL, XML, PubMed NBIB,
  and optional YAML
- Provider-aware normalization metadata and adapters for generic records,
  PubMed/PubMed XML, OpenAlex JSON, and Crossref JSON
- A canonical bibliographic dataset object with raw-record traceability
- Descriptive bibliometric indicators
- Incidence, co-occurrence, collaboration, co-citation, bibliographic coupling,
  and direct-citation matrices
- Network construction, simple node/edge metrics, and export to JSON, CSV,
  GraphML, GEXF, Pajek, and VOSviewer-style edge lists
- Thematic mapping, thematic evolution, conceptual structure, and historiography
- Exports for common tabular and network-analysis workflows

## Installation

```bash
pip install biblioflow
```

Optional YAML support:

```bash
pip install "biblioflow[yaml]"
```

## Python API

```python
import biblioflow as bf

records = bf.load(
    "data/scopus_export.bib",
    provider="scopus",
    format="bibtex",
)

summary = bf.analyze(records)

kw_net = bf.network(
    records,
    kind="co_occurrence",
    unit="keywords_all",
    normalize="association",
    min_occurrences=5,
)

themes = bf.map_themes(records, field="keywords_all")
evolution = bf.trace_themes(records, field="keywords_all", by="publication_year")
```

The main namespace should use Pythonic names such as `load()`, `analyze()`,
`matrix()`, `network()`, `map_themes()`, `trace_themes()`, `historiograph()`,
and `export()`. Bibliometrix-style compatibility helpers live outside the main
namespace under `biblioflow.compat`.

## CLI

The command name is `biblioflow`:

```bash
biblioflow --help
```

Do not use or document a hyphenated command alias.

## Development

```bash
conda env create -f conda/dev.yaml
conda activate biblioflow
cd packages/biblioflow
poetry config virtualenvs.create false
poetry install --extras "dev yaml"
```

From the repository root, run the same workflow through Makim:

```bash
makim tests.linter
makim tests.unit
makim package.build
makim docs.build
makim all.ci
```

## Web application package

The monorepo also contains `packages/biblioflow-web`:

- `packages/biblioflow-web/backend`: FastAPI package published as
  `biblioflow-web`
- `packages/biblioflow-web/frontend`: private React/Vite source app

The frontend is not published to npm. Release builds compile the React app and
copy `frontend/dist/` into the backend package static directory before building
the `biblioflow-web` wheel/sdist.

Useful root Makim tasks:

```bash
makim web.backend.tests
makim web.frontend.install
makim web.frontend.build
makim web.package.build
```

## Notebook widget application

`packages/biblioflow-nb` contains the Jupyter/Colab widget application published
as `biblioflow-nb`:

```python
import biblioflow_nb as bfn

app = bfn.launch()
```

Useful root Makim tasks:

```bash
makim nb.tests
makim nb.package.build
makim nb.examples.check
```

## Project status

The current implementation covers loading, normalization, validation, deduplication, local enrichment, descriptive analysis, matrix/network construction, lightweight thematic helpers, compatibility shims, export, and a CLI.
