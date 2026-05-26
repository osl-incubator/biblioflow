import { Link, useParams } from "react-router-dom";

const exportTypes = [
  ["Dataset", "JSON, CSV, optional YAML"],
  ["Matrices", "CSV and JSON adjacency tables"],
  ["Networks", "GraphML, GEXF, Pajek, VOSviewer"],
  ["Report", "Planned narrative synthesis export"],
];

export function ExportsPage() {
  const { projectId } = useParams();

  return (
    <div className="page-stack">
      <section className="dashboard-hero card">
        <div>
          <span className="eyebrow">Synthesis</span>
          <h1>Report and export center</h1>
          <p>
            Collect datasets, matrices, networks, plots, and report-ready
            outputs from biblioflow analyses.
          </p>
        </div>
        <Link
          className="button button-secondary"
          to={`/projects/${projectId}/dashboard`}
        >
          Back to dashboard
        </Link>
      </section>

      <section className="dashboard-grid export-grid">
        {exportTypes.map(([title, detail]) => (
          <article className="card export-card" key={title}>
            <span className="eyebrow">Export</span>
            <h2>{title}</h2>
            <p>{detail}</p>
            <button type="button">Prepare export</button>
          </article>
        ))}
      </section>
    </div>
  );
}
