# biblioflow-nb

Notebook widget application for `biblioflow` bibliometric workflows.

`biblioflow-nb` provides a Jupyter/Colab-friendly widget UI that mirrors the
core workflow of `biblioflow-web` without running FastAPI, React, or a local web
server. All calculations are delegated to the core `biblioflow` package.

## Quickstart

```python
import biblioflow_nb as bfn

bfn.colab_setup()  # safe outside Google Colab
app = bfn.launch()
```

Launch with an existing dataset:

```python
import biblioflow as bf
import biblioflow_nb as bfn

dataset = bf.load("records.ris")
app = bfn.launch(records=dataset)
```

Import from PubMed/PMC:

```python
import os
import biblioflow_nb as bfn

os.environ["BIBLIOFLOW_NCBI_EMAIL"] = "researcher@example.org"

app = bfn.app(display=False)
app.from_pubmed(query="bibliometrics AND reproducibility", limit=20)
app.from_pmc(query="open science", limit=20)
app.display()
```

The widget app also includes a **PubMed/PMC** panel. API keys can be provided in
the panel or through `BIBLIOFLOW_NCBI_API_KEY`; they are not stored in the
session manifest.

## Development

```bash
cd packages/biblioflow-nb
PYTHONPATH=src:../biblioflow/src pytest --cov=biblioflow_nb --cov-fail-under=90
PYTHONPATH=src:../biblioflow/src python -m ruff check src tests
PYTHONPATH=src:../biblioflow/src python -m mypy src
poetry build
```
