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

This repository currently includes an initial MVP implementation of the core
workflow described in the project plan. Advanced science-mapping features will
continue to evolve.

## Current and planned scope

- MVP file-based ingestion for RIS, BibTeX, CSV/TSV, JSON/JSONL, NBIB, and
  optional YAML; XML and additional provider exports are planned
- Provider-aware normalization metadata for generic files and common provider
  names; deeper Scopus, Web of Science, PubMed Central, OpenAlex, Crossref,
  Lens, Dimensions, and Cochrane mappings are planned
- A canonical bibliographic dataset object with raw-record traceability
- Descriptive bibliometric indicators
- Incidence and co-occurrence matrices in the MVP; collaboration, co-citation,
  bibliographic coupling, and direct-citation matrices are planned
- Network construction, simple node/edge metrics, and export; clustering is planned
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
and `export()`. Compatibility helpers for Bibliometrix-style names, if added,
should live outside the main namespace under `biblioflow.compat`.

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
poetry config virtualenvs.create false
poetry install --extras "dev yaml"
```

Run the same workflow through Makim:

```bash
makim tests.linter
makim tests.unit
makim package.build
makim docs.build
makim all.ci
```

## Project status

The current implementation covers loading, normalization, descriptive analysis, matrix/network construction, lightweight thematic helpers, export, and a small CLI.
