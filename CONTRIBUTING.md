# Contributing

Thank you for contributing to `biblioflow`.

## Development setup

```bash
conda env create -f conda/dev.yaml
conda activate biblioflow
cd packages/biblioflow
poetry config virtualenvs.create false
poetry install --extras "dev yaml"
```

## Checks

From the repository root, run the same core checks used by CI:

```bash
makim tests.linter
makim tests.unit
makim package.build
makim docs.build
```

Web package tasks are also available from the repository root:

```bash
makim web.backend.tests
makim web.frontend.install
makim web.frontend.build
makim web.package.build
```

Notebook app checks:

```bash
makim nb.tests
makim nb.package.build
makim nb.examples.check
```

## Scope

`biblioflow` is being initialized as a Python-native bibliographic metadata and
bibliometrics workflow package inspired by R `bibliometrix`. Keep public APIs
Pythonic and reserve Bibliometrix-style compatibility names for
`biblioflow.compat` only.

Use `biblioflow` as the package, import, and CLI name. Do not add a hyphenated
alias.

## Documentation

Documentation lives in `docs/` and is built with Quarto:

```bash
quarto render docs
```
