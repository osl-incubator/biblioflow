import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useCreateProject, useProjects } from "../api/queries";

export function ProjectPage() {
  const [name, setName] = useState("My bibliometric project");
  const projects = useProjects();
  const createProject = useCreateProject();
  const latestProject = useMemo(
    () => projects.data?.data.at(0),
    [projects.data?.data],
  );

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createProject.mutate(name);
  }

  return (
    <div className="page-stack">
      <section className="dashboard-hero card">
        <div>
          <span className="eyebrow">Workspace</span>
          <h1>Guided project console</h1>
          <p>
            Create a project, upload a bibliographic collection, then unlock the
            appraisal, analysis, and synthesis panels. This screen is an
            intermediate interface while the final product direction evolves.
          </p>
        </div>
        <form onSubmit={onSubmit} className="project-create-form">
          <label>
            Project name
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>
          <button type="submit" disabled={createProject.isPending}>
            {createProject.isPending ? "Creating…" : "Create project"}
          </button>
        </form>
      </section>

      <section className="stat-grid" aria-label="Workspace summary">
        <article className="stat-card accent-search">
          <span>Projects</span>
          <strong>{projects.data?.data.length ?? "—"}</strong>
          <small>active workspaces</small>
        </article>
        <article className="stat-card accent-appraisal">
          <span>Appraisal</span>
          <strong>Filters</strong>
          <small>years, authors, sources, keywords</small>
        </article>
        <article className="stat-card accent-analysis">
          <span>Analysis</span>
          <strong>Overview</strong>
          <small>main information and production</small>
        </article>
        <article className="stat-card accent-synthesis">
          <span>Synthesis</span>
          <strong>Networks</strong>
          <small>conceptual, intellectual, social</small>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="card project-list-card">
          <div className="section-heading compact">
            <span className="eyebrow">Search</span>
            <h2>Projects and collections</h2>
          </div>
          {projects.isLoading && <p>Loading projects…</p>}
          {projects.isError && <p role="alert">Unable to load projects.</p>}
          <ul className="project-list">
            {projects.data?.data.map((project) => (
              <li key={project.project_id}>
                <div>
                  <strong>{project.name}</strong>
                  <span>{project.project_id}</span>
                </div>
                <div className="project-actions">
                  <Link to={`/projects/${project.project_id}/upload`}>
                    Upload
                  </Link>
                  <Link to={`/projects/${project.project_id}/dashboard`}>
                    Dashboard
                  </Link>
                  <Link to={`/projects/${project.project_id}/exports`}>
                    Exports
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        </article>

        <article className="card analysis-menu-card">
          <div className="section-heading compact">
            <span className="eyebrow">Analysis</span>
            <h2>Available panels</h2>
          </div>
          <div className="analysis-menu-grid">
            <div>
              <strong>Overview</strong>
              <span>Main Information, Annual Production, Citations</span>
            </div>
            <div>
              <strong>Sources</strong>
              <span>Relevant Sources, Bradford's Law, Source Dynamics</span>
            </div>
            <div>
              <strong>Authors</strong>
              <span>Productivity, Affiliations, Countries, Lotka's Law</span>
            </div>
            <div>
              <strong>Documents</strong>
              <span>Cited Documents, References, Trend Topics</span>
            </div>
            <div>
              <strong>Knowledge Structures</strong>
              <span>Conceptual, Intellectual, and Social Structure</span>
            </div>
          </div>
        </article>
      </section>

      {latestProject && (
        <section className="card next-step-card">
          <span className="eyebrow">Next step</span>
          <h2>Continue with {latestProject.name}</h2>
          <p>
            Upload files and load a normalized dataset before running the
            dashboard panels.
          </p>
          <Link
            className="button button-primary"
            to={`/projects/${latestProject.project_id}/upload`}
          >
            Upload bibliographic files
          </Link>
        </section>
      )}
    </div>
  );
}
