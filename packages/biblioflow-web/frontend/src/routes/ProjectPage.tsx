import { FormEvent, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { EmptyState } from "../components/common/EmptyState";
import {
  useCreateProject,
  useDeleteProject,
  useProjects,
} from "../api/queries";
import { formatDate } from "./dashboard/utils";

export function ProjectPage() {
  const [name, setName] = useState("My bibliometric project");
  const navigate = useNavigate();
  const projects = useProjects();
  const createProject = useCreateProject();
  const deleteProject = useDeleteProject();
  const sortedProjects = useMemo(
    () =>
      [...(projects.data?.data ?? [])].sort((left, right) =>
        String(right.updated_at).localeCompare(String(left.updated_at)),
      ),
    [projects.data?.data],
  );
  const latestProject = sortedProjects.at(0);

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createProject.mutate(name, {
      onSuccess: (response) => {
        setName("My bibliometric project");
        navigate(`/projects/${response.data.project_id}/upload`);
      },
    });
  }

  return (
    <div className="page-stack">
      <section className="dashboard-hero card">
        <div>
          <span className="eyebrow">Workspace</span>
          <h1>Project console</h1>
          <p>
            Create a project, upload a bibliographic collection, then open the
            appraisal, analysis, and synthesis panels. Project state is stored
            by the FastAPI backend and all computations are delegated to
            biblioflow.
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
          {createProject.isError && (
            <p role="alert">{createProject.error.message}</p>
          )}
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
          {!projects.isLoading && !sortedProjects.length && (
            <EmptyState title="No projects yet" icon="＋">
              <p>
                Create a project above to start uploading bibliographic files.
              </p>
            </EmptyState>
          )}
          <ul className="project-list">
            {sortedProjects.map((project) => (
              <li key={project.project_id}>
                <div className="project-summary">
                  <strong>{project.name}</strong>
                  <span>{project.project_id}</span>
                  <small>Created {formatDate(project.created_at)}</small>
                  <small>Updated {formatDate(project.updated_at)}</small>
                  <small>
                    Active dataset:{" "}
                    {project.active_dataset_id?.slice(0, 8) ?? "none"}
                  </small>
                </div>
                <div className="project-actions">
                  <Link to={`/projects/${project.project_id}/upload`}>
                    Upload
                  </Link>
                  <Link
                    to={`/projects/${project.project_id}/dashboard/overview`}
                  >
                    Dashboard
                  </Link>
                  <Link to={`/projects/${project.project_id}/exports`}>
                    Exports
                  </Link>
                  <button
                    type="button"
                    className="link-button danger-link"
                    disabled={deleteProject.isPending}
                    onClick={() => deleteProject.mutate(project.project_id)}
                  >
                    Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
          {deleteProject.isError && (
            <p role="alert">{deleteProject.error.message}</p>
          )}
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
              <span>Relevant Sources, source dynamics placeholders</span>
            </div>
            <div>
              <strong>Authors</strong>
              <span>Productivity, affiliations, countries placeholders</span>
            </div>
            <div>
              <strong>Documents</strong>
              <span>Record browser, cited documents placeholders</span>
            </div>
            <div>
              <strong>Knowledge Structures</strong>
              <span>
                Conceptual, intellectual, and social matrix/network routes
              </span>
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
