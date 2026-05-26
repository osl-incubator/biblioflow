from pathlib import Path

import biblioflow as bf

DATA = Path(__file__).parent / "data"


def test_load_json_normalizes_records():
    records = bf.load(DATA / "minimal.json")

    assert len(records) == 2
    assert records.metadata["format"] == "json"
    first = records.to_records()[0]
    assert first["doi"] == "10.1000/os1"
    assert first["publication_year"] == 2024
    assert "bibliometrics" in first["keywords_all"]


def test_load_ris_bibtex_csv_and_nbib():
    expected_lengths = {
        "minimal.ris": 2,
        "minimal.bib": 1,
        "minimal.csv": 2,
        "minimal.nbib": 2,
    }
    for filename, expected_length in expected_lengths.items():
        records = bf.load(DATA / filename)
        assert len(records) == expected_length
        assert records.to_records()[0]["title"]


def test_infer_format_and_provider():
    assert bf.infer_format("records.ris") == "ris"
    assert bf.infer_format("records.bib") == "bibtex"
    assert bf.infer_provider("pubmed_records.nbib") == "pubmed"
