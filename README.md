# biblioflow

![CI](https://img.shields.io/github/actions/workflow/status/osl-incubator/biblioflow/ci.yml?logo=github&label=CI)
[![Python Versions](https://img.shields.io/pypi/pyversions/biblioflow)](https://pypi.org/project/biblioflow/)
[![Package Version](https://img.shields.io/pypi/v/biblioflow?color=blue)](https://pypi.org/project/biblioflow/)
![License](https://img.shields.io/pypi/l/biblioflow?color=blue)

`biblioflow` is a planned Python-native toolkit for bibliographic metadata,
bibliometrics, science mapping, and literature-review data workflows. The
project is inspired by the R bibliometrics ecosystem, especially
[`bibliometrix`](https://www.bibliometrix.org/), while aiming for a Pythonic API
and dataframe-centric workflows.

This repository is currently a project scaffold. The full implementation will be
added later. The examples below describe the intended public direction, not a
complete implemented API yet.

## Planned scope

- File-based ingestion for RIS, BibTeX, CSV/TSV, XML, JSON, NBIB, and related
  bibliographic exports
- Provider-aware normalization for Scopus, Web of Science, PubMed, PubMed
  Central, OpenAlex, Crossref, Lens, Dimensions, Cochrane, and generic exports
- A canonical bibliographic dataset object with raw-record traceability
- Descriptive bibliometric indicators
- Incidence, co-occurrence, collaboration, co-citation, bibliographic coupling,
  and direct-citation matrices
- Network construction, metrics, clustering, and export
- Thematic mapping, thematic evolution, conceptual structure, and historiography
- Exports for common tabular and network-analysis workflows

## Installation

Once published:

```bash
pip install biblioflow
```

Optional YAML support is planned as:

```bash
pip install "biblioflow[yaml]"
```

## Intended Python API

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

## Intended CLI

The command name is planned to be `biblioflow`:

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

Core package functionality will be implemented in future changes.
