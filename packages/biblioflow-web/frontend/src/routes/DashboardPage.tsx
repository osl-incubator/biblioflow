import { Link, Navigate, NavLink, Outlet, useLocation } from "react-router-dom";

import { EmptyState } from "../components/common/EmptyState";
import { useDatasetSummary } from "../api/queries";
import { useActiveWorkspace } from "./dashboard/workspace";

const dashboardTabs = [
  ["Overview", "overview"],
  ["Validation", "validation"],
  ["Filters", "filters"],
  ["Sources", "sources"],
  ["Authors", "authors"],
  ["Documents", "documents"],
  ["Words", "words"],
  ["Conceptual", "conceptual-structure"],
  ["Intellectual", "intellectual-structure"],
  ["Social", "social-structure"],
  ["Matrices", "matrices"],
  ["Networks", "networks"],
];

function timespan(start?: number | null, end?: number | null): string {
  if (!start && !end) {
    return "—";
  }
  if (start === end) {
    return String(start);
  }
  return `${start ?? "?"}–${end ?? "?"}`;
}

export function DashboardPage() {
  const { projectId, project, projectQuery, activeDatasetId, hasDataset } =
    useActiveWorkspace();
  const location = useLocation();
  const summary = useDatasetSummary(projectId, activeDatasetId);
  const summaryData = summary.data?.data;

  if (
    projectId &&
    location.pathname.endsWith(`/projects/${projectId}/dashboard`)
  ) {
    return <Navigate to="overview" replace />;
  }

  if (projectQuery.isLoading) {
    return <p>Loading project workspace…</p>;
  }

  if (projectQuery.isError || !projectId) {
    return (
      <EmptyState title="Project not found" icon="!">
        <p>
          Select an existing project or create a new one to open the dashboard.
        </p>
        <Link className="button button-primary" to="/projects">
          Back to projects
        </Link>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack dashboard-layout">
      <section className="dashboard-hero card workspace-banner">
        <div>
          <span className="eyebrow">Analysis workspace</span>
          <h1>{project?.name ?? "Project dashboard"}</h1>
          <p>
            Review the normalized dataset, validate records, apply filters, run
            overview metrics, and prepare matrices or networks from biblioflow.
          </p>
          <div className="workspace-meta">
            <span>Project {projectId.slice(0, 8)}</span>
            <span>
              {activeDatasetId
                ? `Active dataset ${activeDatasetId.slice(0, 8)}`
                : "No active dataset"}
            </span>
          </div>
        </div>
        <div className="run-panel">
          <Link
            className="button button-secondary"
            to={`/projects/${projectId}/upload`}
          >
            Upload files
          </Link>
          <Link
            className="button button-primary"
            to={`/projects/${projectId}/exports`}
          >
            Export results
          </Link>
        </div>
      </section>

      <section className="stat-grid" aria-label="Dataset statistics">
        <article className="stat-card accent-search">
          <span>Documents</span>
          <strong>{summaryData?.documents ?? "—"}</strong>
          <small>normalized records</small>
        </article>
        <article className="stat-card accent-analysis">
          <span>Sources</span>
          <strong>{summaryData?.sources ?? "—"}</strong>
          <small>journals, books, venues</small>
        </article>
        <article className="stat-card accent-appraisal">
          <span>Authors</span>
          <strong>{summaryData?.authors ?? "—"}</strong>
          <small>unique names</small>
        </article>
        <article className="stat-card accent-synthesis">
          <span>Timespan</span>
          <strong>
            {timespan(summaryData?.timespan_start, summaryData?.timespan_end)}
          </strong>
          <small>publication years</small>
        </article>
      </section>

      <nav className="dashboard-subnav" aria-label="Dashboard sections">
        {dashboardTabs.map(([label, path]) => (
          <NavLink key={path} to={`/projects/${projectId}/dashboard/${path}`}>
            {label}
          </NavLink>
        ))}
      </nav>

      {!hasDataset ? (
        <EmptyState title="Load a dataset to unlock dashboard panels" icon="⇪">
          <p>
            Upload one or more bibliographic export files, then load them into a
            normalized biblioflow dataset. All analysis routes will use the
            active dataset stored on this project.
          </p>
          <Link
            className="button button-primary"
            to={`/projects/${projectId}/upload`}
          >
            Upload bibliographic files
          </Link>
        </EmptyState>
      ) : (
        <Outlet />
      )}
    </div>
  );
}
