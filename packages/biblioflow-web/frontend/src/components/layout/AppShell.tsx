import { NavLink, Outlet } from "react-router-dom";

import "../../styles/app.css";
import { navigationSections } from "./navigation";

export function AppShell() {
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
                {section.items.map((item) => (
                  <li key={`${section.label}-${item.label}`}>
                    {item.path && !item.disabled ? (
                      <NavLink to={item.path} className="nav-item">
                        <span>{item.label}</span>
                        {item.detail && <small>{item.detail}</small>}
                      </NavLink>
                    ) : (
                      <span className="nav-item nav-item-disabled">
                        <span>{item.label}</span>
                        {item.detail && <small>{item.detail}</small>}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </nav>
      </aside>

      <div className="app-workspace">
        <header className="app-header">
          <div>
            <strong>Science Mapping Workflow</strong>
            <span>Search → Appraisal → Analysis → Synthesis</span>
          </div>
          <nav aria-label="Primary navigation">
            <NavLink to="/">Home</NavLink>
            <NavLink to="/projects">Projects</NavLink>
          </nav>
        </header>
        <main className="app-main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
