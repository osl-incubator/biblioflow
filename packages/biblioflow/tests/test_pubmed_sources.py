import json
import sys
import types
from pathlib import Path
from typing import Any, ClassVar

import pytest

import biblioflow as bf
from biblioflow.exceptions import APIConfigurationError
from biblioflow.load.infer import normalize_provider_name
from biblioflow.sources.pubmed import (
    coerce_pymedx_article,
    normalize_pmc_article,
    normalize_pubmed_article,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeArticle:
    def __init__(self, **values: Any) -> None:
        self.__dict__.update(values)


class FakePubMed:
    calls: ClassVar[list[dict[str, Any]]] = []
    articles: ClassVar[list[Any]] = []
    total_results: ClassVar[int] = 0
    query_uses_total_count: ClassVar[bool] = True

    def __init__(self, *, tool: str, email: str, api_key: str) -> None:
        self.calls.append({"tool": tool, "email": email, "api_key": api_key})
        self.parameters = {"tool": tool, "email": email, "db": "pubmed"}
        if api_key:
            self.parameters["api_key"] = api_key

    def getTotalResultsCount(self, query: str) -> int:
        self.calls.append({"total_query": query})
        return self.total_results

    def query(self, query: str, max_results: int = 100) -> list[Any]:
        self.calls.append({"query": query, "max_results": max_results})
        if self.query_uses_total_count:
            self.getTotalResultsCount(query)
        return self.articles


class FakePubMedCentral(FakePubMed):
    calls: ClassVar[list[dict[str, Any]]] = []
    articles: ClassVar[list[Any]] = []
    total_results: ClassVar[int] = 0
    query_uses_total_count: ClassVar[bool] = False

    def __init__(self, *, tool: str, email: str, api_key: str) -> None:
        super().__init__(tool=tool, email=email, api_key=api_key)
        self.parameters["db"] = "pmc"


class FakePymedxArticle:
    __slots__ = (
        "abstract",
        "authors",
        "doi",
        "journal",
        "keywords",
        "publication_date",
        "pubmed_id",
        "title",
    )

    def __init__(self, **values: Any) -> None:
        for key in self.__slots__:
            setattr(self, key, values.get(key))

    def toDict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__slots__}


def _install_fake_pymedx(monkeypatch: pytest.MonkeyPatch) -> None:
    module = types.ModuleType("pymedx")
    module.PubMed = FakePubMed
    module.PubMedCentral = FakePubMedCentral
    FakePubMed.calls = []
    FakePubMedCentral.calls = []
    FakePubMed.total_results = 0
    FakePubMedCentral.total_results = 0
    FakePubMed.query_uses_total_count = True
    FakePubMedCentral.query_uses_total_count = False
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


def test_coerce_real_pymedx_style_article_metadata() -> None:
    article = FakePymedxArticle(
        pubmed_id="99999999",
        title="PyMedX slot metadata",
        abstract="Article abstract",
        journal="Journal of PyMedX",
        doi="10.1000/pymedx",
        keywords=["metadata", "pubmed"],
        publication_date="2026-05-29",
        authors=[{"firstname": "Ada", "lastname": "Lovelace"}],
    )

    coerced = coerce_pymedx_article(article)
    normalized = normalize_pubmed_article(article)
    dataset = bf.load([normalized], source="pubmed")
    row = dataset.to_records()[0]

    assert coerced["pubmed_id"] == "99999999"
    assert row["pmid"] == "99999999"
    assert row["doi"] == "10.1000/pymedx"
    assert row["title"] == "PyMedX slot metadata"
    assert row["source_title"] == "Journal of PyMedX"
    assert row["authors"] == ["Ada Lovelace"]


def test_from_pubmed_uses_pymedx_client_and_returns_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_pymedx(monkeypatch)
    article = json.loads((FIXTURES / "pubmed" / "pubmed_article_full.json").read_text())
    FakePubMed.articles = [FakeArticle(**article), article]
    FakePubMed.total_results = 42

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
    assert dataset.metadata["remote_source"] == "pubmed"
    assert dataset.metadata["query"] == "bibliometrics"
    assert dataset.metadata["requested_limit"] == 1
    assert dataset.metadata["returned_count"] == 1
    assert dataset.metadata["total_results"] == 42
    assert dataset.metadata["client_package"] == "pymedx"
    assert dataset.metadata["api_key_present"] is True
    assert "secret" not in json.dumps(dataset.metadata)
    assert FakePubMed.calls[0] == {
        "tool": "biblioflow-tests",
        "email": "tester@example.org",
        "api_key": "secret",
    }
    assert FakePubMed.calls[1] == {"query": "bibliometrics", "max_results": 1}
    assert FakePubMed.calls[2] == {"total_query": "bibliometrics"}


def test_from_pubmed_central_and_alias_use_environment_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_pymedx(monkeypatch)
    article = json.loads((FIXTURES / "pmc" / "pmc_article_full_text.json").read_text())
    FakePubMedCentral.articles = [article]
    FakePubMedCentral.total_results = 7
    monkeypatch.setenv("BIBLIOFLOW_NCBI_EMAIL", "env@example.org")
    monkeypatch.setenv("BIBLIOFLOW_NCBI_API_KEY", "env-key")

    dataset = bf.from_pubmed_central(query="open science", limit=10)
    alias_dataset = bf.from_pmc(query="open science", limit=10)

    assert dataset.to_records()[0]["pmcid"] == "PMC7654321"
    assert alias_dataset.to_records()[0]["pmcid"] == "PMC7654321"
    assert dataset.metadata["total_results"] == 7
    assert dataset.metadata["remote_source"] == "pmc"
    assert dataset.metadata["ncbi_database"] == "pmc"
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
