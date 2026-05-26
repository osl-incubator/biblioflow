import { Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { DashboardPage } from "./routes/DashboardPage";
import { ExportsPage } from "./routes/ExportsPage";
import { HomePage } from "./routes/HomePage";
import { ProjectPage } from "./routes/ProjectPage";
import { UploadPage } from "./routes/UploadPage";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="projects" element={<ProjectPage />} />
        <Route path="projects/:projectId/upload" element={<UploadPage />} />
        <Route path="projects/:projectId/dashboard/*" element={<DashboardPage />} />
        <Route path="projects/:projectId/exports" element={<ExportsPage />} />
      </Route>
    </Routes>
  );
}
