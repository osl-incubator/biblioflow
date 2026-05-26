import { Link } from "react-router-dom";

import { StatusPanel } from "../components/feedback/StatusPanel";
import { useHealth } from "../api/queries";

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
              Start a project
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
