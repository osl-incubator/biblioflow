from pathlib import Path

import biblioflow as bf

DATA = Path(__file__).parent / "data"


def test_summarize_dataset_and_import():
    dataset = bf.load(DATA / "minimal.json")

    summary = bf.summarize_dataset(dataset)
    assert summary.documents == 2
    assert summary.authors == 3
    assert summary.timespan_start == 2024
    assert summary.timespan_end == 2025

    import_summary = bf.summarize_import(dataset)
    assert import_summary.records == 2
    assert import_summary.format == "json"


def test_filter_dataset_and_options():
    dataset = bf.load(DATA / "minimal.json")

    options = bf.available_filter_values(dataset)
    assert 2024 in options.years
    assert "Journal of Open Research" in options.sources
    assert "bibliometrics" in options.keywords

    filtered = bf.filter_dataset(dataset, bf.DatasetFilterSpec(year_min=2025))
    assert filtered.input_records == 2
    assert filtered.output_records == 1
    assert filtered.dataset.to_records()[0]["publication_year"] == 2025

    by_keyword = bf.filter_dataset(dataset, {"keywords": ["open science"]})
    assert by_keyword.output_records == 1
    assert by_keyword.to_dict()["summary"]["documents"] == 1
