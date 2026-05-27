import json
from pathlib import Path

import pytest

import biblioflow as bf
from biblioflow.exceptions import APIConfigurationError, OptionalDependencyError
from biblioflow.providers import parse_crossref_date, reconstruct_openalex_abstract
from biblioflow.sources.crossref import normalize_crossref_work
from biblioflow.sources.scopus_api import normalize_scopus_api_result

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_accepts_source_alias_keyword_for_scopus_csv():
    dataset = bf.load(
        FIXTURES / "scopus" / "scopus_basic.csv",
        source="scopus",
    )

    row = dataset.to_records()[0]
    assert dataset.metadata["provider"] == "scopus"
    assert row["source_id"] == "2-s2.0-123"
    assert row["doi"] == "10.1234/scopus"
    assert row["source_title"] == "Journal of Bibliometrics"
    assert row["publication_year"] == 2024
    assert row["authors"] == ["Jane Smith", "John Doe"]
    assert "science mapping" in row["keywords_all"]
    assert row["raw"]["EID"] == "2-s2.0-123"


def test_load_wos_plain_text_detects_multiline_and_repeated_fields():
    dataset = bf.load(FIXTURES / "wos" / "savedrecs_basic.txt")

    row = dataset.to_records()[0]
    assert dataset.metadata["provider"] == "web_of_science"
    assert row["source_id"] == "WOS:0000001"
    assert row["title"] == "Science mapping with Python and reproducible bibliometrics"
    assert row["doi"] == "10.1234/example"
    assert row["authors"] == ["Jane Smith", "John Doe"]
    assert row["references_raw"][0].startswith("Author A")
    assert row["reference_count"] == 2
    assert row["cited_by_count"] == 12
    assert row["wos_categories"] == ["Information Science & Library Science"]


def test_openalex_helpers_reconstruct_abstract_and_normalize_work():
    work = json.loads(
        (FIXTURES / "openalex" / "work_with_abstract_inverted_index.json").read_text()
    )
    assert (
        reconstruct_openalex_abstract(work["abstract_inverted_index"])
        == "Bibliometrics is useful"
    )

    dataset = bf.load([work], source="openalex")
    row = dataset.to_records()[0]
    assert row["abstract"] == "Bibliometrics is useful"
    assert row["source_title"] == "OpenAlex Journal"
    assert row["open_access_status"] == "gold"
    assert row["institutions"] == ["Open University"]
    assert row["countries"] == ["US"]


def test_crossref_helpers_parse_dates_references_and_funders():
    work = json.loads((FIXTURES / "crossref" / "work_with_references.json").read_text())
    assert parse_crossref_date(work) == "2024-05-10"

    normalized = normalize_crossref_work(work)
    dataset = bf.load([normalized], source="crossref")
    row = dataset.to_records()[0]
    assert row["doi"] == "10.1234/crossref"
    assert row["publication_date"] == "2024-05-10"
    assert row["publication_year"] == 2024
    assert row["authors"] == ["Jane Smith"]
    assert row["references"][0] == "10.1000/ref1"
    assert row["funders"][0].startswith("{'name': 'Open Funder'}")


def test_scopus_api_normalizer_and_optional_connector_error():
    result = json.loads(
        (FIXTURES / "scopus_api" / "search_result_basic.json").read_text()
    )
    normalized = normalize_scopus_api_result(result)
    dataset = bf.load([normalized], source="scopus_api")
    row = dataset.to_records()[0]
    assert row["source_id"] == "2-s2.0-999"
    assert row["doi"] == "10.1234/api"
    assert row["source_title"] == "API Journal"
    assert row["cited_by_count"] == 4

    with pytest.raises((APIConfigurationError, OptionalDependencyError)):
        bf.from_scopus(query="TITLE-ABS-KEY(bibliometrics)", limit=1)
