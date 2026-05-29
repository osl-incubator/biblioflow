import { FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { DataTable } from "../components/common/DataTable";
import { EmptyState } from "../components/common/EmptyState";
import { downloadExportUrl, downloadReportUrl } from "../api/client";
import {
  useCreateExport,
  useCreateReport,
  useExports,
  useProject,
  useReports,
} from "../api/queries";
import type { ReportCompleteness } from "../api/types";
import { formatDate } from "./dashboard/utils";

const exportFormats = ["json", "csv"];
const reportCompletenessOptions: ReportCompleteness[] = [
  "summary",
  "standard",
  "complete",
];

const exportTypes = [
  ["Dataset", "JSON or CSV normalized records", true],
  ["Matrices", "CSV and JSON adjacency tables", false],
  ["Networks", "GraphML, GEXF, Pajek, VOSviewer", false],
  ["Report", "Professional Quarto/Typst PDF report", true],
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
  const reportsQuery = useReports(projectId);
  const createExport = useCreateExport(projectId);
  const createReport = useCreateReport(projectId);
  const [format, setFormat] = useState("json");
  const [reportTitle, setReportTitle] = useState("");
  const [reportSubtitle, setReportSubtitle] = useState(
    "Bibliometric project report",
  );
  const [reportCompleteness, setReportCompleteness] =
    useState<ReportCompleteness>("standard");
  const activeDatasetId = project.data?.data.active_dataset_id ?? null;
  const defaultReportTitle = project.data?.data.name
    ? `${project.data.data.name} report`
    : "biblioflow project report";

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

  function onCreateReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeDatasetId) {
      return;
    }
    createReport.mutate({
      dataset_id: activeDatasetId,
      title: reportTitle.trim() || defaultReportTitle,
      subtitle: reportSubtitle.trim() || null,
      authors: [],
      template: "modern",
      completeness: reportCompleteness,
      render: true,
      keep_qmd: false,
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
            Dataset exports and professional PDF reports are available now;
            matrix and network exporters remain available through their
            dashboard panels.
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
        <div className="export-form-stack">
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

          <form className="card form-card" onSubmit={onCreateReport}>
            <div className="section-heading compact">
              <span className="eyebrow">PDF report</span>
              <h2>Generate project report</h2>
              <p>
                Build a polished Quarto QMD report rendered with Typst. The
                report includes methods, PRISMA flow, tables, field coverage,
                warnings, and reproducibility metadata.
              </p>
            </div>
            <p className="muted-copy">
              Active dataset: {activeDatasetId?.slice(0, 8) ?? "none"}
            </p>
            <label>
              Title
              <input
                placeholder={defaultReportTitle}
                value={reportTitle}
                onChange={(event) => setReportTitle(event.target.value)}
              />
            </label>
            <label>
              Subtitle
              <input
                value={reportSubtitle}
                onChange={(event) => setReportSubtitle(event.target.value)}
              />
            </label>
            <label>
              Completeness
              <select
                value={reportCompleteness}
                onChange={(event) =>
                  setReportCompleteness(
                    event.target.value as ReportCompleteness,
                  )
                }
              >
                {reportCompletenessOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="submit"
              className="button-primary"
              disabled={!activeDatasetId || createReport.isPending}
            >
              {createReport.isPending ? "Generating…" : "Generate PDF report"}
            </button>
            {!activeDatasetId && (
              <p className="muted-copy">
                Load a dataset before creating reports.
              </p>
            )}
            {createReport.isError && (
              <p role="alert">{createReport.error.message}</p>
            )}
            {createReport.isSuccess && (
              <p className="muted-copy" role="status">
                Report generated. Download it from the reports table below.
              </p>
            )}
          </form>
        </div>

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
          <span className="eyebrow">Reports</span>
          <h2>Generated PDF reports</h2>
        </div>
        {reportsQuery.isLoading && <p>Loading reports…</p>}
        {reportsQuery.isError && <p role="alert">Unable to load reports.</p>}
        {reportsQuery.data?.data.length ? (
          <DataTable
            rows={reportsQuery.data.data}
            columns={[
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
                key: "warnings",
                header: "Warnings",
                render: (row) => row.warnings?.length ?? 0,
              },
              {
                key: "download",
                header: "Download",
                render: (row) => (
                  <a href={downloadReportUrl(projectId, row.filename)} download>
                    Download PDF
                  </a>
                ),
              },
            ]}
          />
        ) : (
          !reportsQuery.isLoading && (
            <EmptyState title="No reports yet" icon="▣">
              <p>Generate a PDF report to create the first report artifact.</p>
            </EmptyState>
          )
        )}
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
