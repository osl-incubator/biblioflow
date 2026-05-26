from __future__ import annotations

from biblioflow_nb.state import NotebookExport, NotebookSession, NotebookUpload


def test_session_manifest_tracks_uploads_and_exports(tmp_path):
    session = NotebookSession()
    upload = NotebookUpload(name="records.ris", path=tmp_path / "records.ris", size=12)
    export = NotebookExport(
        name="records.json",
        path=tmp_path / "records.json",
        kind="dataset",
        format="json",
    )

    session.add_upload(upload)
    session.add_export(export)
    manifest = session.to_manifest()

    assert manifest["session_id"] == session.session_id
    assert manifest["uploads"][0]["name"] == "records.ris"
    assert manifest["exports"][0]["kind"] == "dataset"


def test_session_clear_resets_dataset_state():
    session = NotebookSession(active_dataset=object(), active_dataset_name="x")

    session.clear()

    assert session.active_dataset is None
    assert session.active_dataset_name is None
    assert session.analysis_cache == {}
