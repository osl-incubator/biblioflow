import json
import math
from pathlib import Path

import biblioflow as bf
from biblioflow.cli import main

DATA = Path(__file__).parent / "data"


def test_analyze_matrix_network_and_themes():
    records = bf.load(DATA / "minimal.json")
    summary = bf.analyze(records)
    assert summary.main_information["documents"] == 2
    assert summary.main_information["authors"] == 3

    mat = bf.matrix(records, unit="keywords_all")
    assert mat.table.loc["bibliometrics", "open science"] == 1

    net = bf.network(records, unit="keywords_all")
    assert len(net.nodes) >= 2
    assert any(
        edge["source"] == "bibliometrics" or edge["target"] == "bibliometrics"
        for edge in net.edges.to_dict(orient="records")
    )

    thematic = bf.map_themes(records)
    assert "theme" in thematic.to_dataframe().columns
    assert len(bf.conceptual_structure(records).to_dataframe()) >= 2

    evolution = bf.trace_themes(records)
    assert len(evolution.to_dataframe()) >= 2


def test_analyze_ignores_missing_and_nan_years():
    dataset = bf.load(
        [
            {"title": "Complete record", "publication_year": 2024},
            {"title": "Missing year", "publication_year": None},
            {"title": "NaN year", "publication_year": math.nan},
        ],
        source="generic",
    )

    summary = bf.analyze(dataset)
    assert summary.main_information["documents"] == 3
    assert summary.main_information["timespan_start"] == 2024
    assert summary.main_information["timespan_end"] == 2024
    assert summary.annual_production.to_dict(orient="records") == [
        {"publication_year": 2024, "documents": 1}
    ]


def test_export_dataset_and_network(tmp_path):
    records = bf.load(DATA / "minimal.json")
    output = tmp_path / "records.json"
    bf.export(records, output)
    assert json.loads(output.read_text())[0]["title"]

    graphml = tmp_path / "network.graphml"
    bf.export(bf.network(records, unit="keywords_all"), graphml)
    assert "<graphml" in graphml.read_text()


def test_cli_analyze_and_convert(tmp_path, capsys):
    assert main(["analyze", str(DATA / "minimal.json"), "--top-n", "2"]) == 0
    captured = capsys.readouterr()
    assert '"documents": 2' in captured.out

    output = tmp_path / "records.csv"
    assert (
        main(["convert", str(DATA / "minimal.json"), "-o", str(output), "--to", "csv"])
        == 0
    )
    assert output.exists()
