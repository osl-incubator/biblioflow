import { NavLink, Outlet } from "react-router-dom";

import "../../styles/app.css";

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <strong>biblioflow-web</strong>
          <span>Bibliometric workflows powered by biblioflow</span>
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
  );
}
