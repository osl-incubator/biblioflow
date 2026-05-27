import json
import sys
import types
from pathlib import Path
from typing import Any, ClassVar

import pytest

import biblioflow as bf
from biblioflow.exceptions import APIConfigurationError
from biblioflow.load.infer import normalize_provider_name
from biblioflow.sources.pubmed import normalize_pmc_article, normalize_pubmed_article

FIXTURES = Path(__file__).parent / "fixtures"


class FakeArticle:
    def __init__(self, **values: Any) -> None:
        self.__dict__.update(values)


class FakePubMed:
    calls: ClassVar[list[dict[str, Any]]] = []
    articles: ClassVar[list[Any]] = []

    def __init__(self, *, tool: str, email: str, api_key: str) -> None:
        self.calls.append({"tool": tool, "email": email, "api_key": api_key})

    def query(self, query: str, max_results: int = 100) -> list[Any]:
        self.calls.append({"query": query, "max_results": max_results})
        return self.articles


class FakePubMedCentral(FakePubMed):
    calls: ClassVar[list[dict[str, Any]]] = []
    articles: ClassVar[list[Any]] = []


def _install_fake_pymedx(monkeypatch: pytest.MonkeyPatch) -> None:
    module = types.ModuleType("pymedx")
    module.PubMed = FakePubMed
    module.PubMedCentral = FakePubMedCentral
    FakePubMed.calls = []
    FakePubMedCentral.calls = []
    monkeypatch.setitem(sys.modules, "pymedx", module)


def test_normalize_pubmed_article_maps_identifiers_and_metadata() -> None:
    article = json.loads((FIXTURES / "pubmed" / "pubmed_article_full.json").read_text())

    normalized = normalize_pubmed_article(article)
    dataset = bf.load([normalized], source="pubmed")
    row = dataset.to_records()[0]

    assert row["source"] == "pubmed"
    assert row["source_id"] == "12345678"
    assert row["pmid"] == "12345678"
    assert row["pmcid"] == "PMC1234567"
    assert row["doi"] == "10.1000/pubmed"
    assert row["publication_date"] == "2024-05-10"
    assert row["publication_year"] == 2024
    assert row["authors"] == ["Jane Smith", "John Doe"]
    assert "Bibliometrics" in row["keywords_index"]
    assert row["url"] == "https://pubmed.ncbi.nlm.nih.gov/12345678/"
    assert row["open_access_url"].endswith("/PMC1234567/")


def test_normalize_pmc_article_maps_full_text_and_urls() -> None:
    article = json.loads((FIXTURES / "pmc" / "pmc_article_full_text.json").read_text())

    normalized = normalize_pmc_article(article)
    dataset = bf.load([normalized], source="pmc")
    row = dataset.to_records()[0]

    assert row["source"] == "pmc"
    assert row["source_id"] == "PMC7654321"
    assert row["pmcid"] == "PMC7654321"
    assert row["pmid"] == "87654321"
    assert row["doi"] == "10.1000/pmc"
    assert row["full_text"].startswith("Introduction.")
    assert row["url"] == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7654321/"
    assert row["full_text_url"] == row["url"]


def test_from_pubmed_uses_pymedx_client_and_returns_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_pymedx(monkeypatch)
    article = json.loads((FIXTURES / "pubmed" / "pubmed_article_full.json").read_text())
    FakePubMed.articles = [FakeArticle(**article), article]

    dataset = bf.from_pubmed(
        query="bibliometrics",
        limit=1,
        tool="biblioflow-tests",
        email="tester@example.org",
        api_key="secret",
    )
    row = dataset.to_records()[0]

    assert len(dataset) == 1
    assert row["pmid"] == "12345678"
    assert FakePubMed.calls[0] == {
        "tool": "biblioflow-tests",
        "email": "tester@example.org",
        "api_key": "secret",
    }
    assert FakePubMed.calls[1] == {"query": "bibliometrics", "max_results": 1}


def test_from_pubmed_central_and_alias_use_environment_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_pymedx(monkeypatch)
    article = json.loads((FIXTURES / "pmc" / "pmc_article_full_text.json").read_text())
    FakePubMedCentral.articles = [article]
    monkeypatch.setenv("BIBLIOFLOW_NCBI_EMAIL", "env@example.org")
    monkeypatch.setenv("BIBLIOFLOW_NCBI_API_KEY", "env-key")

    dataset = bf.from_pubmed_central(query="open science", limit=10)
    alias_dataset = bf.from_pmc(query="open science", limit=10)

    assert dataset.to_records()[0]["pmcid"] == "PMC7654321"
    assert alias_dataset.to_records()[0]["pmcid"] == "PMC7654321"
    assert FakePubMedCentral.calls[0]["email"] == "env@example.org"
    assert FakePubMedCentral.calls[0]["api_key"] == "env-key"


def test_from_pubmed_requires_contact_email(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BIBLIOFLOW_NCBI_EMAIL", raising=False)
    monkeypatch.delenv("NCBI_EMAIL", raising=False)
    monkeypatch.delenv("ENTREZ_EMAIL", raising=False)

    with pytest.raises(APIConfigurationError, match="contact email"):
        bf.from_pubmed(query="bibliometrics")


def test_pubmed_source_options_dataframe_raw_and_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_pymedx(monkeypatch)
    article = json.loads((FIXTURES / "pubmed" / "pubmed_article_full.json").read_text())
    FakePubMed.articles = [article]

    frame = bf.from_pubmed(
        query="bibliometrics",
        email="tester@example.org",
        as_dataframe=True,
    )
    dataset = bf.from_pubmed(
        query="bibliometrics",
        email="tester@example.org",
        keep_raw=False,
    )

    assert frame.to_dict(orient="records")[0]["pmid"] == "12345678"
    assert dataset.to_records()[0]["raw"] is None
    assert normalize_provider_name("pubmed-central") == "pmc"
    assert normalize_provider_name("pubmedcentral") == "pmc"
    assert normalize_provider_name("pmcid") == "pmc"
