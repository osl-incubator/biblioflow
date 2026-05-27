import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { DataTable } from "../components/common/DataTable";
import { EmptyState } from "../components/common/EmptyState";
import { downloadExportUrl } from "../api/client";
import { useCreateExport, useExports, useProject } from "../api/queries";
import { formatDate } from "./dashboard/utils";

const exportFormats = ["json", "csv"];

const exportTypes = [
  ["Dataset", "JSON or CSV normalized records", true],
  ["Matrices", "CSV and JSON adjacency tables", false],
  ["Networks", "GraphML, GEXF, Pajek, VOSviewer", false],
  ["Report", "Planned narrative synthesis export", false],
] as const;

function formatSize(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function ExportsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const project = useProject(projectId);
  const exportsQuery = useExports(projectId);
  const createExport = useCreateExport(projectId);
  const [format, setFormat] = useState("json");
  const activeDatasetId = project.data?.data.active_dataset_id ?? null;

  function onCreateDatasetExport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeDatasetId) {
      return;
    }
    createExport.mutate({
      dataset_id: activeDatasetId,
      kind: "dataset",
      format,
    });
  }

  if (project.isLoading) {
    return <p>Loading export center…</p>;
  }

  if (project.isError || !projectId) {
    return (
      <EmptyState title="Project not found" icon="!">
        <p>Select a project before preparing exports.</p>
        <Link className="button button-primary" to="/projects">
          Back to projects
        </Link>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack">
      <section className="dashboard-hero card">
        <div>
          <span className="eyebrow">Synthesis</span>
          <h1>Export center</h1>
          <p>
            Generate downloadable artifacts from the active biblioflow dataset.
            Matrix, network, and report exports are represented in the UI and
            should be wired after those backend exporters are expanded.
          </p>
        </div>
        <Link
          className="button button-secondary"
          to={`/projects/${projectId}/dashboard/overview`}
        >
          Back to dashboard
        </Link>
      </section>

      <section className="dashboard-grid export-grid-wide">
        <form className="card form-card" onSubmit={onCreateDatasetExport}>
          <div className="section-heading compact">
            <span className="eyebrow">Dataset export</span>
            <h2>Prepare normalized records</h2>
          </div>
          <p className="muted-copy">
            Active dataset: {activeDatasetId?.slice(0, 8) ?? "none"}
          </p>
          <label>
            Format
            <select
              value={format}
              onChange={(event) => setFormat(event.target.value)}
            >
              {exportFormats.map((option) => (
                <option key={option} value={option}>
                  {option.toUpperCase()}
                </option>
              ))}
            </select>
          </label>
          <button
            type="submit"
            className="button-primary"
            disabled={!activeDatasetId || createExport.isPending}
          >
            {createExport.isPending ? "Preparing…" : "Create dataset export"}
          </button>
          {!activeDatasetId && (
            <p className="muted-copy">
              Load a dataset before creating exports.
            </p>
          )}
          {createExport.isError && (
            <p role="alert">{createExport.error.message}</p>
          )}
        </form>

        <div className="export-card-grid">
          {exportTypes.map(([title, detail, enabled]) => (
            <article className="card export-card" key={title}>
              <span className="eyebrow">
                {enabled ? "Available" : "Planned"}
              </span>
              <h2>{title}</h2>
              <p>{detail}</p>
              {!enabled && (
                <button type="button" disabled>
                  Prepare export
                </button>
              )}
            </article>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="section-heading compact">
          <span className="eyebrow">Artifacts</span>
          <h2>Generated exports</h2>
        </div>
        {exportsQuery.isLoading && <p>Loading exports…</p>}
        {exportsQuery.isError && <p role="alert">Unable to load exports.</p>}
        {exportsQuery.data?.data.length ? (
          <DataTable
            rows={exportsQuery.data.data}
            columns={[
              { key: "kind", header: "Kind" },
              { key: "format", header: "Format" },
              { key: "filename", header: "Filename" },
              {
                key: "size",
                header: "Size",
                render: (row) => formatSize(row.size),
              },
              {
                key: "created_at",
                header: "Created",
                render: (row) => formatDate(row.created_at),
              },
              {
                key: "download",
                header: "Download",
                render: (row) => (
                  <a href={downloadExportUrl(projectId, row.filename)} download>
                    Download
                  </a>
                ),
              },
            ]}
          />
        ) : (
          !exportsQuery.isLoading && (
            <EmptyState title="No exports yet" icon="⇩">
              <p>Create a dataset export to make the first artifact.</p>
            </EmptyState>
          )
        )}
      </section>
    </div>
  );
}
