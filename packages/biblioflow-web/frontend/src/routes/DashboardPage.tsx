import { Link, useParams } from "react-router-dom";

const overviewStats = [
  { label: "Documents", value: "—", detail: "load a dataset" },
  { label: "Sources", value: "—", detail: "journals and books" },
  { label: "Authors", value: "—", detail: "normalized names" },
  { label: "Timespan", value: "—", detail: "publication years" },
];

const panels = [
  {
    section: "Overview",
    title: "Main Information",
    description:
      "Documents, sources, authors, keywords, citations, and annual scientific production.",
  },
  {
    section: "Sources",
    title: "Source analysis",
    description:
      "Most relevant sources, local impact, Bradford's Law, and source dynamics over time.",
  },
  {
    section: "Authors",
    title: "Author analysis",
    description:
      "Most relevant authors, production over time, affiliations, countries, and collaboration indicators.",
  },
  {
    section: "Documents",
    title: "Document analysis",
    description:
      "Most cited documents, cited references, reference spectroscopy, and trend topics.",
  },
  {
    section: "Conceptual Structure",
    title: "Co-word and thematic maps",
    description:
      "Keyword co-occurrence, thematic map, thematic evolution, and conceptual structure placeholders.",
  },
  {
    section: "Intellectual Structure",
    title: "Citation structures",
    description:
      "Co-citation, bibliographic coupling, direct citations, and historiograph panels.",
  },
  {
    section: "Social Structure",
    title: "Collaboration networks",
    description:
      "Author, affiliation, and country collaboration networks with map-oriented placeholders.",
  },
];

export function DashboardPage() {
  const { projectId } = useParams();

  return (
    <div className="page-stack">
      <section className="dashboard-hero card">
        <div>
          <span className="eyebrow">Analysis</span>
          <h1>Project dashboard</h1>
          <p>
            Guided analysis workspace for project {projectId}. The structure is
            ready for biblioflow-powered API responses as the core analytics
            expand.
          </p>
        </div>
        <div className="run-panel">
          <button type="button">Run Analysis</button>
          <Link to={`/projects/${projectId}/exports`}>Export results</Link>
        </div>
      </section>

      <section className="stat-grid" aria-label="Dataset statistics">
        {overviewStats.map((stat) => (
          <article className="stat-card" key={stat.label}>
            <span>{stat.label}</span>
            <strong>{stat.value}</strong>
            <small>{stat.detail}</small>
          </article>
        ))}
      </section>

      <section className="analysis-workbench">
        <aside className="analysis-tabs" aria-label="Dashboard sections">
          {panels.map((panel) => (
            <a
              href={`#${panel.section.toLowerCase().replaceAll(" ", "-")}`}
              key={panel.section}
            >
              {panel.section}
            </a>
          ))}
        </aside>
        <div className="analysis-panels">
          {panels.map((panel) => (
            <article
              className="card analysis-panel"
              id={panel.section.toLowerCase().replaceAll(" ", "-")}
              key={panel.section}
            >
              <span className="eyebrow">{panel.section}</span>
              <h2>{panel.title}</h2>
              <p>{panel.description}</p>
              <div className="placeholder-visual">
                <span />
                <span />
                <span />
                <span />
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
