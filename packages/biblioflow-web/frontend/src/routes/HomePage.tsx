import { Link } from "react-router-dom";

import { StatusPanel } from "../components/feedback/StatusPanel";
import { useHealth, useProjects } from "../api/queries";
import { formatDate } from "./dashboard/utils";

const workflowSteps = [
  {
    label: "Search",
    title: "Import your collection",
    text: "Upload records from Scopus, Web of Science, PubMed, OpenAlex, RIS, BibTeX, CSV, JSON, XML, or NBIB exports.",
    accent: "search",
  },
  {
    label: "Appraisal",
    title: "Validate and filter",
    text: "Inspect load warnings, refine by years, sources, authors, keywords, countries, and citation thresholds.",
    accent: "appraisal",
  },
  {
    label: "Analysis",
    title: "Run bibliometrics",
    text: "Review main information, annual production, top sources, authors, documents, and word indicators.",
    accent: "analysis",
  },
  {
    label: "Synthesis",
    title: "Map knowledge structures",
    text: "Explore conceptual, intellectual, and social structures through matrices, networks, maps, and exports.",
    accent: "synthesis",
  },
];

const capabilityCards = [
  "Main Information",
  "Annual Scientific Production",
  "Three-Field Plot",
  "Sources' Impact",
  "Authors' Production",
  "Trend Topics",
  "Thematic Map",
  "Collaboration Networks",
];

export function HomePage() {
  const health = useHealth();
  const projects = useProjects();
  const recentProjects = [...(projects.data?.data ?? [])]
    .sort((left, right) =>
      String(right.updated_at).localeCompare(String(left.updated_at)),
    )
    .slice(0, 3);

  return (
    <div className="page-stack">
      <section className="hero workflow-hero">
        <div className="hero-copy">
          <span className="eyebrow">
            Bibliometric Analysis for Systematic Literature Reviews
          </span>
          <h1>Bibliometric analysis in the browser</h1>
          <p>
            A temporary guided interface for biblioflow: import collections,
            appraise records, run core metrics, and prepare synthesis outputs
            from one guided workspace.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/projects">
              Create or open a project
            </Link>
            <Link
              className="button button-secondary"
              to="/projects#existing-projects"
            >
              Open existing project
            </Link>
            <a className="button button-secondary" href="#workflow">
              View workflow
            </a>
          </div>
        </div>
        <div className="hero-panel" aria-label="Workflow summary">
          <div className="mini-window-bar">
            <span />
            <span />
            <span />
          </div>
          <div className="mini-dashboard">
            <strong>SAAS workflow</strong>
            <ol>
              <li>Search</li>
              <li>Appraisal</li>
              <li>Analysis</li>
              <li>Synthesis</li>
            </ol>
          </div>
        </div>
      </section>

      <section className="dashboard-grid" aria-label="Project access">
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Workspace</span>
            <h2>Select an existing project</h2>
            <p>
              Continue from a saved project before uploading more files or
              opening the analysis dashboard.
            </p>
          </div>
          {projects.isLoading && <p>Loading saved projects…</p>}
          {projects.isError && <p role="alert">Unable to load projects.</p>}
          {!projects.isLoading && !recentProjects.length && (
            <p className="muted-copy">
              No saved projects were found. Create one from the project console
              to start a workspace.
            </p>
          )}
          {!!recentProjects.length && (
            <ul className="project-list">
              {recentProjects.map((project) => {
                const openPath = project.active_dataset_id
                  ? `/projects/${project.project_id}/dashboard/overview`
                  : `/projects/${project.project_id}/upload`;
                return (
                  <li key={project.project_id}>
                    <div className="project-summary">
                      <strong>{project.name}</strong>
                      <span>{project.project_id}</span>
                      <small>Updated {formatDate(project.updated_at)}</small>
                    </div>
                    <div className="project-actions">
                      <Link to={openPath}>Open project</Link>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
          <div className="section-actions project-access-actions">
            <Link className="button button-secondary" to="/projects">
              View all projects
            </Link>
          </div>
        </article>

        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">New workspace</span>
            <h2>Create a new project</h2>
            <p>
              Use the project console to name a workspace, upload bibliographic
              records, and load the first normalized dataset.
            </p>
          </div>
          <Link className="button button-primary" to="/projects">
            Go to project console
          </Link>
        </article>
      </section>

      <section
        className="workflow-grid"
        id="workflow"
        aria-label="SAAS workflow"
      >
        {workflowSteps.map((step, index) => (
          <article
            className={`workflow-card accent-${step.accent}`}
            key={step.label}
          >
            <span className="workflow-index">0{index + 1}</span>
            <strong>{step.label}</strong>
            <h2>{step.title}</h2>
            <p>{step.text}</p>
          </article>
        ))}
      </section>

      <section className="card">
        <div className="section-heading">
          <span className="eyebrow">Analysis menu</span>
          <h2>Guided analysis areas</h2>
          <p>
            The visual structure follows the guided workflow grouping while all
            computations remain delegated to the Python biblioflow library.
          </p>
        </div>
        <div className="capability-grid">
          {capabilityCards.map((item) => (
            <span className="capability-pill" key={item}>
              {item}
            </span>
          ))}
        </div>
      </section>

      <StatusPanel
        title="Backend status"
        tone={health.data ? "success" : "info"}
      >
        {health.isLoading && <p>Checking API status…</p>}
        {health.isError && <p role="alert">The API is not reachable.</p>}
        {health.data && (
          <dl className="status-grid">
            <div>
              <dt>Service</dt>
              <dd>{health.data.service}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{health.data.status}</dd>
            </div>
            <div>
              <dt>Web version</dt>
              <dd>{health.data.version}</dd>
            </div>
            <div>
              <dt>biblioflow</dt>
              <dd>{health.data.biblioflow_version ?? "unknown"}</dd>
            </div>
          </dl>
        )}
      </StatusPanel>
    </div>
  );
}
