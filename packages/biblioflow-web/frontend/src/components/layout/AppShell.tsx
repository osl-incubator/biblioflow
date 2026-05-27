import { NavLink, Outlet, useLocation, useMatch } from "react-router-dom";

import { useProject } from "../../api/queries";
import "../../styles/app.css";
import { navigationSections } from "./navigation";

function routeLabel(segment: string): string {
  return segment
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function useProjectIdFromRoute(): string | null {
  const projectMatch = useMatch("/projects/:projectId/*");
  return projectMatch?.params.projectId ?? null;
}

export function AppShell() {
  const location = useLocation();
  const projectId = useProjectIdFromRoute();
  const projectQuery = useProject(projectId);
  const project = projectQuery.data?.data;
  const activeDatasetId = project?.active_dataset_id ?? null;
  const pathSegments = location.pathname.split("/").filter(Boolean);

  const breadcrumbs =
    pathSegments.length === 0
      ? [{ label: "Home", to: "/" }]
      : [
          { label: "Projects", to: "/projects" },
          ...(project
            ? [
                {
                  label: project.name,
                  to: `/projects/${project.project_id}/dashboard`,
                },
              ]
            : []),
          ...pathSegments
            .filter((segment) => !["projects", projectId].includes(segment))
            .map((segment, index, segments) => ({
              label: routeLabel(segment),
              to:
                index === segments.length - 1
                  ? location.pathname
                  : `/projects/${projectId}/${segments
                      .slice(0, index + 1)
                      .join("/")}`,
            })),
        ];

  return (
    <div className="app-shell">
      <aside
        className="app-sidebar"
        aria-label="Bibliometric workflow navigation"
      >
        <NavLink to="/" className="brand-card" aria-label="biblioflow-web home">
          <span className="brand-mark">bf</span>
          <span>
            <strong>biblioflow</strong>
            <small>Guided science-mapping workspace</small>
          </span>
        </NavLink>

        <div className="workspace-mini-card">
          <span className="eyebrow">Workspace</span>
          <strong>{project?.name ?? "No active project"}</strong>
          <small>
            {activeDatasetId
              ? `Dataset ${activeDatasetId.slice(0, 8)}`
              : projectId
              ? "Upload and load a dataset"
              : "Select or create a project"}
          </small>
        </div>

        <nav className="sidebar-nav" aria-label="Workflow sections">
          <NavLink to="/" className="sidebar-home">
            <span>⌂</span>
            <span>Welcome</span>
          </NavLink>
          {navigationSections.map((section) => (
            <section className="nav-section" key={section.label}>
              <h2 className={`nav-section-title accent-${section.accent}`}>
                <span>{section.icon}</span>
                {section.label}
              </h2>
              <ul>
                {section.items.map((item) => {
                  const requiresProject =
                    item.requiresProject ?? Boolean(item.buildPath);
                  const disabled =
                    item.disabled || (requiresProject && !projectId);
                  const path = projectId
                    ? item.buildPath?.(projectId) ?? item.fallbackPath
                    : item.fallbackPath;

                  return (
                    <li key={`${section.label}-${item.label}`}>
                      {path && !disabled ? (
                        <NavLink to={path} className="nav-item">
                          <span>{item.label}</span>
                          {item.detail && <small>{item.detail}</small>}
                        </NavLink>
                      ) : (
                        <span
                          className="nav-item nav-item-disabled"
                          title={
                            item.disabled
                              ? "This section is planned for a later iteration."
                              : "Select or create a project first."
                          }
                        >
                          <span>{item.label}</span>
                          {item.detail && <small>{item.detail}</small>}
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
            </section>
          ))}
        </nav>
      </aside>

      <div className="app-workspace">
        <header className="app-header">
          <div className="header-copy">
            <strong>Science Mapping Workflow</strong>
            <span>Search → Appraisal → Analysis → Synthesis</span>
            <nav className="breadcrumbs" aria-label="Breadcrumbs">
              {breadcrumbs.map((crumb, index) => (
                <span key={`${crumb.label}-${index}`}>
                  {index > 0 && <em>/</em>}
                  <NavLink to={crumb.to}>{crumb.label}</NavLink>
                </span>
              ))}
            </nav>
          </div>
        </header>
        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
