import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest

import biblioflow as bf
from biblioflow.core.dataset import BibliographicDataset
from biblioflow.core.frames import MatrixFrame, RecordFrame
from biblioflow.core.warnings import LoadWarning
from biblioflow.export import export
from biblioflow.io.json import read_json_records, read_jsonl_records
from biblioflow.io.nbib import read_nbib_records
from biblioflow.io.ris import read_ris_records
from biblioflow.io.xml import read_xml_records
from biblioflow.io.yaml import read_yaml_records
from biblioflow.load.infer import infer_format, infer_provider
from biblioflow.mapping.historiograph import historiograph
from biblioflow.normalize.authors import parse_author_list
from biblioflow.normalize.dates import parse_publication_date, parse_year
from biblioflow.normalize.ids import normalize_doi
from biblioflow.normalize.text import clean_text, normalize_language, split_keywords
from biblioflow.sources import bibtex, crossref, openalex, ris, scopus, scopus_api, wos

DATA = Path(__file__).parent / "data"
FIXTURES = Path(__file__).parent / "fixtures"


def test_record_frame_and_matrix_frame_fallback_helpers(tmp_path: Path) -> None:
    frame = RecordFrame([{"a": 1}, {"b": 2}], columns=["a", "b"])

    assert len(frame) == 2
    assert not frame.empty
    assert frame.copy().to_dict() == [{"a": 1, "b": None}, {"a": None, "b": 2}]
    assert next(iter(frame.iterrows())) == (0, {"a": 1, "b": None})
    assert frame.to_dict(orient="list") == {"a": [1, None], "b": [None, 2]}
    assert '"a"' in frame.to_json(indent=2)
    with pytest.raises(ValueError, match="Unsupported orient"):
        frame.to_dict(orient="columns")

    csv_path = tmp_path / "records.csv"
    frame.to_csv(csv_path, index=True)
    assert csv_path.read_text().splitlines()[0] == "index,a,b"
    assert frame.select_columns(["b"]).to_dict() == [{"b": None}, {"b": 2}]
    assert frame.rename(columns={"a": "alpha"}).columns == ["alpha", "b"]
    assert RecordFrame([]).empty

    matrix = MatrixFrame(["x", "y"], fill=1)
    assert not matrix.empty
    assert matrix.loc["x", "y"] == 1
    matrix.loc["x", "y"] = 2
    matrix.increment("x", "y", 3)
    assert matrix.get("x", "y") == 5
    assert matrix.copy().to_dict()["x"]["y"] == 5
    assert matrix.to_dict(orient="records")[0]["term"] == "x"
    assert '"x"' in matrix.to_json(indent=2)
    with pytest.raises(ValueError, match="Unsupported orient"):
        matrix.to_dict(orient="columns")

    matrix_csv = tmp_path / "matrix.csv"
    matrix.to_csv(matrix_csv)
    assert matrix_csv.read_text().splitlines()[0] == "term,x,y"
    matrix.to_csv(tmp_path / "matrix-no-index.csv", index=False)
    assert MatrixFrame([]).empty


def test_dataset_and_normalization_edge_helpers(tmp_path: Path) -> None:
    warning = LoadWarning(
        code="demo",
        count=1,
        severity="warning",
        message="Demo warning",
        field="title",
    )
    dataset = BibliographicDataset.from_records(
        [
            {
                "title": "Title A",
                "doi": "10.1000/a",
                "source_id": "SRC1",
                "authors": ["Jane Smith"],
                "keywords_all": ["bibliometrics"],
                "publication_year": "2024",
                "source_title": "Journal A",
            }
        ],
        warnings=[warning],
        metadata={"format": "records", "provider": "generic"},
    )

    assert next(iter(dataset))["title"] == "Title A"
    assert dataset.to_dataframe(schema="bibliometrix").to_dict(orient="records")
    assert "Demo warning" in str(dataset.warning_dicts())
    assert "Title A" in dataset.to_json(tmp_path / "dataset.json")
    dataset.to_csv(tmp_path / "dataset.csv")
    with pytest.raises(ValueError, match="Unsupported schema"):
        dataset.to_records(schema="custom")

    assert bf.summarize_dataset(dataset).to_dict()["documents"] == 1
    assert bf.summarize_import(dataset).to_dict()["provider"] == "generic"

    with pytest.raises(ValueError, match="Only keep"):
        bf.deduplicate(dataset, keep="last")
    assert bf.deduplicate(dataset, by="source_id").metadata["duplicates_removed"] == 0
    enriched = bf.enrich(
        dataset,
        [{"title": "Title A", "publisher": "Publisher A"}],
        by="title",
    )
    assert enriched.to_records()[0]["publisher"] == "Publisher A"

    assert parse_year([]) is None
    assert parse_year({"date-parts": [[2024, 5, 10]]}) == 2024
    assert parse_publication_date({"date-parts": [[2024, 5, 10]]}) == "2024-05-10"
    assert parse_publication_date({"date-parts": [[2024, 5]]}) == "2024-05"
    assert parse_publication_date({"date-parts": [[2024]]}) == "2024"
    assert parse_publication_date("") is None
    assert parse_publication_date("not a date") is None
    assert parse_publication_date("2024/05/10") == "2024-05-10"

    assert normalize_doi([]) is None
    assert normalize_doi("") is None
    assert normalize_doi("doi: 10.1234/ABC.") == "10.1234/abc"
    assert clean_text([]) is None
    assert split_keywords(None) == []
    assert split_keywords(["alpha; beta", "ALPHA", ""]) == ["alpha", "beta"]
    assert normalize_language("fr") == "French"
    assert parse_author_list(None) == []
    assert parse_author_list("   ") == []
    assert [
        author["name"] for author in parse_author_list("Smith,Doe", source="scopus")
    ] == [
        "Smith",
        "Doe",
    ]
    assert len(parse_author_list(["Jane Smith", "Jane Smith"])) == 1


def test_source_file_helpers_and_scopus_api_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert bibtex.can_load(DATA / "minimal.bib")
    bib_content = tmp_path / "records.txt"
    bib_content.write_text("@book{key, title={A Book}}", encoding="utf-8")
    assert bibtex.can_load(bib_content)
    assert not bibtex.can_load(tmp_path / "missing.txt")
    assert bibtex.load_bibtex(DATA / "minimal.bib")[0]["title"]
    assert bibtex.normalize_bibtex_entry({"title": "A"}) == {"title": "A"}

    assert ris.can_load(DATA / "minimal.ris")
    ris_content = tmp_path / "records.txt"
    ris_content.write_text("TY  - JOUR\nTI  - Title\nER  -\n", encoding="utf-8")
    assert ris.can_load(ris_content)
    assert not ris.can_load(tmp_path / "missing.txt")
    assert ris.load_ris(DATA / "minimal.ris")[0]["title"]
    assert ris.normalize_ris_entry({"TY": "JOUR"}) == {"TY": "JOUR"}

    scopus_csv = FIXTURES / "scopus" / "scopus_basic.csv"
    assert scopus.can_load(scopus_csv)
    assert scopus.can_load(tmp_path / "scopus-export.bib")
    assert not scopus.can_load(tmp_path / "notes.txt")
    bad_csv = tmp_path / "bad.csv"
    bad_csv.write_text("only,one\n", encoding="utf-8")
    assert not scopus.can_load(bad_csv)
    assert scopus.load_scopus_csv(scopus_csv)[0]["source_id"] == "2-s2.0-123"
    assert scopus.normalize_scopus_row({"Title": "Scopus row"})["title"] == "Scopus row"
    scopus_bib = tmp_path / "scopus-record.bib"
    scopus_bib.write_text((DATA / "minimal.bib").read_text(), encoding="utf-8")
    assert scopus.load_scopus_bibtex(scopus_bib)[0]["title"]

    wos_file = FIXTURES / "wos" / "savedrecs_basic.txt"
    assert wos.can_load(wos_file)
    assert not wos.can_load(tmp_path / "missing.txt")
    assert wos.load_wos(wos_file)[0]["source_id"] == "WOS:0000001"

    scopus_fixture = json.loads(
        (FIXTURES / "scopus_api" / "search_result_basic.json").read_text()
    )

    class AsDictResult:
        def _asdict(self) -> dict[str, Any]:
            return dict(scopus_fixture)

    class ObjectResult:
        def __init__(self, values: dict[str, Any]) -> None:
            self.__dict__.update(values)

    class FakeSearch:
        def __init__(self, query: str, *, refresh: bool, subscriber: bool) -> None:
            self.query = query
            self.refresh = refresh
            self.subscriber = subscriber
            self.results = [
                AsDictResult(),
                dict(scopus_fixture),
                ObjectResult(scopus_fixture),
            ]

    scopus_module = types.ModuleType("pybliometrics.scopus")
    scopus_module.ScopusSearch = FakeSearch
    monkeypatch.setitem(sys.modules, "pybliometrics", types.ModuleType("pybliometrics"))
    monkeypatch.setitem(sys.modules, "pybliometrics.scopus", scopus_module)

    dataset = scopus_api.from_scopus(query="TITLE(biblioflow)", limit=3)
    assert len(dataset) == 3
    assert dataset.to_records()[0]["source_id"] == "2-s2.0-999"


def test_crossref_and_openalex_query_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    crossref_work = json.loads(
        (FIXTURES / "crossref" / "work_with_references.json").read_text()
    )
    requested_urls: list[str] = []

    def fake_crossref_request(url: str) -> dict[str, Any]:
        requested_urls.append(url)
        return {"message": {"items": [crossref_work]}}

    monkeypatch.setattr(crossref, "_request_json", fake_crossref_request)
    crossref_dataset = crossref.from_crossref(
        query="science mapping",
        filter={"from-pub-date": "2024-01-01"},
        limit=1,
        mailto="tester@example.org",
    )
    assert crossref_dataset.to_records()[0]["doi"] == "10.1234/crossref"
    assert "mailto=tester" in requested_urls[0]

    openalex_work = json.loads(
        (FIXTURES / "openalex" / "work_with_abstract_inverted_index.json").read_text()
    )
    openalex_calls = 0

    def fake_openalex_request(url: str) -> dict[str, Any]:
        nonlocal openalex_calls
        openalex_calls += 1
        if openalex_calls == 1:
            assert "search=science" in url
            assert "sort=cited_by_count" in url
            return {"results": [openalex_work], "meta": {"next_cursor": "next"}}
        return {"results": []}

    monkeypatch.setattr(openalex, "_request_json", fake_openalex_request)
    openalex_dataset = openalex.from_openalex(
        search="science",
        filter={"from_publication_date": "2024-01-01"},
        sort="cited_by_count",
        limit=2,
        per_page=1,
        mailto="tester@example.org",
    )
    assert len(openalex_dataset) == 1
    assert openalex_dataset.to_records()[0]["source_title"] == "OpenAlex Journal"


def test_structured_readers_cover_edge_shapes(tmp_path: Path) -> None:
    message_json = tmp_path / "message.json"
    message_json.write_text(
        json.dumps({"message": {"DOI": "10/one"}}), encoding="utf-8"
    )
    assert read_json_records(message_json) == [{"DOI": "10/one"}]

    object_json = tmp_path / "object.json"
    object_json.write_text(
        json.dumps({"items": [{"id": 1}], "ignored": True}), encoding="utf-8"
    )
    assert read_json_records(object_json) == [{"id": 1}]

    scalar_json = tmp_path / "scalar.json"
    scalar_json.write_text("42", encoding="utf-8")
    with pytest.raises(ValueError, match="object or a list"):
        read_json_records(scalar_json)

    jsonl = tmp_path / "records.jsonl"
    jsonl.write_text('\n{"a": 1}\n[1, 2]\n{"b": 2}\n', encoding="utf-8")
    assert read_jsonl_records(jsonl) == [{"a": 1}, {"b": 2}]

    yaml_list = tmp_path / "records.yaml"
    yaml_list.write_text("- title: A\n- title: B\n- 2\n", encoding="utf-8")
    assert read_yaml_records(yaml_list) == [{"title": "A"}, {"title": "B"}]
    yaml_dict = tmp_path / "one.yaml"
    yaml_dict.write_text("records:\n  - title: C\n", encoding="utf-8")
    assert read_yaml_records(yaml_dict) == [{"title": "C"}]
    yaml_scalar = tmp_path / "scalar.yaml"
    yaml_scalar.write_text("plain text", encoding="utf-8")
    assert read_yaml_records(yaml_scalar) == []

    nbib = tmp_path / "edge.nbib"
    nbib.write_text(
        "PMID- 1\n"
        "TI  - PubMed title\n"
        "      continued\n"
        "AID - PMC123 [pmcid]\n"
        "AID - 10.1000/test [doi]\n"
        "AID - ignored value\n"
        "IS  - 1234-5678 (Print)\n"
        "IS  - 8765-4321 (Electronic)\n"
        "AU  - Jane Smith\n\n",
        encoding="utf-8",
    )
    nbib_row = read_nbib_records(nbib)[0]
    assert nbib_row["title"] == "PubMed title continued"
    assert nbib_row["pmcid"] == "PMC123"
    assert nbib_row["doi"] == "10.1000/test"
    assert nbib_row["eissn"] == "8765-4321"

    ris_file = tmp_path / "edge.ris"
    ris_file.write_text(
        "TY  - JOUR\nTI  - First line\nSecond line\nKW  - one\nKW  - two\n",
        encoding="utf-8",
    )
    ris_row = read_ris_records(ris_file)[0]
    assert ris_row["title"] == "First line Second line"
    assert ris_row["keywords_author"] == ["one", "two"]

    generic_xml = tmp_path / "records.xml"
    generic_xml.write_text(
        "<root><record><title>A</title><title>B</title><empty /></record>"
        "<Record><title>C</title></Record></root>",
        encoding="utf-8",
    )
    assert read_xml_records(generic_xml)[0]["title"] == ["A", "B"]

    root_xml = tmp_path / "root.xml"
    root_xml.write_text(
        "<article><title>Root title</title></article>", encoding="utf-8"
    )
    assert read_xml_records(root_xml) == [{"title": "Root title"}]

    pubmed_xml = tmp_path / "pubmed.xml"
    pubmed_xml.write_text(
        "<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>9</PMID>"
        "<Article><ArticleTitle>XML title</ArticleTitle>"
        "<Journal><Title>XML Journal</Title>"
        "<ISSN IssnType='electronic'>1111-2222</ISSN>"
        "<JournalIssue><PubDate><Year>2024</Year><Month>5</Month></PubDate>"
        "<Volume>1</Volume><Issue>2</Issue></JournalIssue></Journal>"
        "<AuthorList><Author><CollectiveName>Group Author</CollectiveName>"
        "</Author></AuthorList>"
        "<ELocationID EIdType='doi'>10/xml</ELocationID>"
        "<Abstract><AbstractText>Abstract text</AbstractText></Abstract>"
        "<Language>eng</Language></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>",
        encoding="utf-8",
    )
    pubmed_row = read_xml_records(pubmed_xml)[0]
    assert pubmed_row["authors"] == ["Group Author"]
    assert pubmed_row["publication_date"] == "2024-05"
    assert pubmed_row["eissn"] == "1111-2222"


def test_inference_matrix_historiograph_and_export_paths(tmp_path: Path) -> None:
    bib_like = tmp_path / "unknown.records"
    bib_like.write_text("@article{a, title={A}}", encoding="utf-8")
    assert infer_format(bib_like) == "bibtex"
    ris_like = tmp_path / "unknown.data"
    ris_like.write_text("TY  - JOUR\nER  -\n", encoding="utf-8")
    assert infer_format(ris_like) == "ris"
    wos_like = tmp_path / "savedrecs.txt"
    wos_like.write_text("FN Clarivate\nPT J\n", encoding="utf-8")
    assert infer_format(wos_like) == "plain_text"
    assert infer_format(tmp_path / "missing.unknown") == "unknown"

    openalex_csv = tmp_path / "openalex.csv"
    openalex_csv.write_text("id,doi,publication_year\n1,10/x,2024\n", encoding="utf-8")
    assert infer_provider(openalex_csv, format="csv") == "openalex"
    assert (
        infer_provider(tmp_path / "my-wos-export.bib", format="bibtex")
        == "web_of_science"
    )
    assert (
        infer_provider(tmp_path / "my-scopus-export.bib", format="bibtex") == "scopus"
    )
    assert infer_provider(DATA / "minimal.ris", format="ris") == "ris"
    assert infer_provider(wos_like, format="plain-text") == "web_of_science"
    assert infer_provider(tmp_path / "lens_export.data", format="unknown") == "lens"

    crossref_json = tmp_path / "crossref.json"
    crossref_json.write_text(
        json.dumps({"message-type": "work", "DOI": "10/x"}), encoding="utf-8"
    )
    assert infer_provider(crossref_json, format="json") == "crossref"
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not json", encoding="utf-8")
    assert infer_provider(bad_json, format="json") == "generic"

    records = bf.load(
        [
            {
                "title": "A long cited document title",
                "doi": "10/a",
                "authors": ["One", "Two"],
                "keywords": ["alpha", "beta"],
                "references": ["10/z"],
            },
            {
                "title": "Document B",
                "doi": "10/b",
                "authors": ["Two"],
                "keywords": ["alpha", "beta"],
                "references": ["10/a", "A long cited document title"],
            },
        ]
    )

    incidence = bf.matrix(records, kind="incidence", unit="keywords_all")
    assert incidence.to_dataframe().to_dict(orient="records")[0]["alpha"] == 1
    association = bf.matrix(
        records, kind="co_occurrence", unit="keywords_all", normalize="association"
    )
    assert association.table.loc["alpha", "beta"] == 0.5
    co_citation = bf.matrix(records, kind="co_citation")
    assert co_citation.unit == "references"
    with pytest.raises(ValueError, match="Unknown unit"):
        bf.matrix(records, unit="missing")
    with pytest.raises(ValueError, match="Unsupported matrix kind"):
        bf.matrix(records, kind="unknown", unit="keywords_all")

    graph = historiograph(records)
    assert graph.metadata["records"] == 2
    assert graph.network.edges.to_dict(orient="records")[0]["target"] == "10/a"

    dataset_csv = tmp_path / "dataset.csv"
    export(records, dataset_csv, format="csv")
    assert dataset_csv.exists()
    matrix_csv = tmp_path / "matrix.csv"
    export(association, matrix_csv, format="csv")
    assert matrix_csv.exists()
    matrix_json = tmp_path / "matrix.json"
    export(association, matrix_json, format="json")
    assert "alpha" in matrix_json.read_text()

    network = bf.network(records, kind="collaboration")
    network_dir = tmp_path / "network-csv"
    export(network, network_dir, format="csv")
    assert (network_dir / "nodes.csv").exists()
    network_json = tmp_path / "network.json"
    export(network, network_json, format="json")
    assert "nodes" in network_json.read_text()

    class CsvObject:
        def to_csv(self, path: Path, *, index: bool = False) -> None:
            path.write_text(f"index={index}\n", encoding="utf-8")

    class JsonObject:
        def to_json(self, *, orient: str, indent: int) -> str:
            return json.dumps({"orient": orient, "indent": indent})

    export(CsvObject(), tmp_path / "object.csv", format="csv")
    export(JsonObject(), tmp_path / "object.json", format="json")
    raw_json = tmp_path / "raw.json"
    export({"created": object()}, raw_json, format="json")
    assert "created" in raw_json.read_text()
    with pytest.raises(ValueError, match="Unsupported export format"):
        export(object(), tmp_path / "object.txt", format="txt")
