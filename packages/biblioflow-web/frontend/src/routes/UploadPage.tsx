import { Link, useParams } from "react-router-dom";

const supportedSources = [
  "Scopus",
  "Web of Science",
  "PubMed",
  "OpenAlex",
  "Crossref",
  "RIS",
  "BibTeX",
  "CSV/JSON/XML/NBIB",
];

export function UploadPage() {
  const { projectId } = useParams();

  return (
    <div className="page-stack">
      <section className="dashboard-hero card">
        <div>
          <span className="eyebrow">Search</span>
          <h1>Import or load data</h1>
          <p>
            This guided search panel stages bibliographic file upload and
            dataset loading. The backend routes are ready; richer controls will
            be wired progressively.
          </p>
        </div>
        <Link
          className="button button-secondary"
          to={`/projects/${projectId}/dashboard`}
        >
          Go to dashboard
        </Link>
      </section>

      <section className="upload-layout">
        <article className="card upload-dropzone">
          <span className="dropzone-icon">⇪</span>
          <h2>Upload bibliographic files</h2>
          <p>
            Drag-and-drop controls will connect to project uploads. For now, use
            this screen as the guided Search step in the workflow.
          </p>
          <button type="button">Choose files</button>
        </article>
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Supported files</span>
            <h2>Database exports</h2>
          </div>
          <div className="capability-grid compact-grid">
            {supportedSources.map((source) => (
              <span className="capability-pill" key={source}>
                {source}
              </span>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
