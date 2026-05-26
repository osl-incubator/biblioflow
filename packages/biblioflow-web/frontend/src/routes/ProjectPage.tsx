import { FormEvent, useState } from "react";

import { useCreateProject, useProjects } from "../api/queries";

export function ProjectPage() {
  const [name, setName] = useState("My bibliometric project");
  const projects = useProjects();
  const createProject = useCreateProject();

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createProject.mutate(name);
  }

  return (
    <div className="page-stack">
      <section className="card">
        <h1>Projects</h1>
        <form onSubmit={onSubmit} className="inline-form">
          <label>
            Project name
            <input value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <button type="submit" disabled={createProject.isPending}>
            Create project
          </button>
        </form>
      </section>

      <section className="card">
        <h2>Existing projects</h2>
        {projects.isLoading && <p>Loading projects…</p>}
        {projects.isError && <p role="alert">Unable to load projects.</p>}
        <ul>
          {projects.data?.data.map((project) => (
            <li key={project.project_id}>
              <strong>{project.name}</strong>
              <span>{project.project_id}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
