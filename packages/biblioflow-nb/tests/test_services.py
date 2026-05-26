from __future__ import annotations

from biblioflow_nb.services import (
    AnalysisService,
    DatasetService,
    ExportService,
    MatrixService,
    NetworkService,
)
from biblioflow_nb.state import NotebookSession


def test_dataset_analysis_matrix_network_and_export_services(data_dir, tmp_path):
    session = NotebookSession()
    datasets = DatasetService(session)
    analysis = AnalysisService(session, datasets)
    matrices = MatrixService(session, datasets)
    networks = NetworkService(session, datasets)
    exports = ExportService(session, datasets)

    dataset = datasets.load(data_dir / "minimal.json")
    assert len(dataset) == 2
    assert datasets.summary()["documents"] == 2

    filter_result = datasets.apply_filters({"year_min": 2025})
    assert filter_result["output_records"] == 1
    datasets.reset_filters()

    overview = analysis.overview(top_n=2)
    assert overview["main_information"]["documents"] == 2

    matrix = matrices.build(unit="keywords_all")
    assert matrix.kind == "co_occurrence"

    network = networks.build(unit="keywords_all")
    assert len(network.nodes) > 0

    output = exports.export_dataset(tmp_path / "records.json")
    assert output.exists()
    assert session.exports[-1].format == "json"
