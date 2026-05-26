from pathlib import Path

import biblioflow as bf
from biblioflow.cli import main
from biblioflow.compat.bibliometrix import biblio_analysis, convert2df

DATA = Path(__file__).parent / "data"


def test_xml_openalex_and_crossref_loading():
    xml_records = bf.load(DATA / "minimal_pubmed.xml", provider="pubmed")
    assert len(xml_records) == 1
    assert xml_records.to_records()[0]["source_id"] == "123456"
    assert "Bibliometrics" in xml_records.to_records()[0]["keywords_all"]

    openalex = bf.load(DATA / "openalex.json", provider="openalex")
    row = openalex.to_records()[0]
    assert row["doi"] == "10.1000/oa1"
    assert row["source_title"] == "OpenAlex Journal"
    assert row["cited_by_count"] == 12
    assert row["affiliations"] == ["Open University"]

    crossref = bf.load(DATA / "crossref.json", provider="crossref")
    row = crossref.to_records()[0]
    assert row["publication_year"] == 2023
    assert row["references"] == ["10.1000/os1"]


def test_deduplicate_enrich_and_compatibility_helpers():
    records = bf.load(DATA / "minimal.json")
    duplicated = bf.load([*records.to_records(), records.to_records()[0]])
    deduped = bf.deduplicate(duplicated)
    assert len(deduped) == 2
    assert deduped.metadata["duplicates_removed"] == 1

    enriched = bf.enrich(
        records,
        {"10.1000/os1": {"publisher": "Open Science Press"}},
        by="doi",
    )
    assert enriched.to_records()[0]["publisher"] == "Open Science Press"

    frame = convert2df(DATA / "minimal.json")
    assert len(frame) == 2
    assert biblio_analysis(records).main_information["documents"] == 2


def test_citation_matrices_and_extra_exports(tmp_path):
    records = bf.load(
        [
            {
                "title": "A",
                "doi": "10/a",
                "year": 2020,
                "references": ["10/x", "10/y"],
                "authors": ["One"],
            },
            {
                "title": "B",
                "doi": "10/b",
                "year": 2021,
                "references": ["10/x", "10/a"],
                "authors": ["One", "Two"],
            },
        ]
    )
    coupling = bf.matrix(records, kind="bibliographic_coupling")
    assert coupling.table.loc["10/a", "10/b"] == 1

    direct = bf.matrix(records, kind="direct_citation")
    assert direct.table.loc["10/b", "10/a"] == 1

    collaboration = bf.matrix(records, kind="collaboration")
    assert collaboration.unit == "authors"
    assert collaboration.table.loc["One", "Two"] == 1

    net = bf.network(records, kind="collaboration")
    for suffix, fmt in [
        ("network.gexf", None),
        ("network.net", None),
        ("network.txt", "vosviewer"),
    ]:
        output = tmp_path / suffix
        bf.export(net, output, format=fmt)
        assert output.exists()


def test_cli_validate_matrix_and_network(tmp_path, capsys):
    assert main(["validate", str(DATA / "minimal.json")]) == 0
    assert '"records": 2' in capsys.readouterr().out

    matrix_out = tmp_path / "matrix.csv"
    assert main(["matrix", str(DATA / "minimal.json"), "-o", str(matrix_out)]) == 0
    assert matrix_out.exists()

    network_out = tmp_path / "network.gexf"
    assert (
        main(
            [
                "network",
                str(DATA / "minimal.json"),
                "-o",
                str(network_out),
                "--to",
                "gexf",
            ]
        )
        == 0
    )
    assert "<gexf" in network_out.read_text()
