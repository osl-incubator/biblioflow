import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { DashboardPage } from "./routes/DashboardPage";
import { ExportsPage } from "./routes/ExportsPage";
import { HomePage } from "./routes/HomePage";
import { ProjectPage } from "./routes/ProjectPage";
import { UploadPage } from "./routes/UploadPage";
import { AuthorsPage } from "./routes/dashboard/AuthorsPage";
import { DocumentsPage } from "./routes/dashboard/DocumentsPage";
import { FiltersPage } from "./routes/dashboard/FiltersPage";
import { MatrixPage } from "./routes/dashboard/MatrixPage";
import { NetworkPage } from "./routes/dashboard/NetworkPage";
import { OverviewPage } from "./routes/dashboard/OverviewPage";
import { PrismaPage } from "./routes/dashboard/PrismaPage";
import { SourcesPage } from "./routes/dashboard/SourcesPage";
import { StructurePage } from "./routes/dashboard/StructurePage";
import { ValidationPage } from "./routes/dashboard/ValidationPage";
import { WordsPage } from "./routes/dashboard/WordsPage";

export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="projects" element={<ProjectPage />} />
        <Route path="projects/:projectId/upload" element={<UploadPage />} />
        <Route path="projects/:projectId/dashboard" element={<DashboardPage />}>
          <Route index element={<Navigate to="overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="sources" element={<SourcesPage />} />
          <Route path="authors" element={<AuthorsPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="words" element={<WordsPage />} />
          <Route
            path="conceptual-structure"
            element={<StructurePage kind="conceptual" />}
          />
          <Route
            path="intellectual-structure"
            element={<StructurePage kind="intellectual" />}
          />
          <Route
            path="social-structure"
            element={<StructurePage kind="social" />}
          />
          <Route path="matrices" element={<MatrixPage />} />
          <Route path="networks" element={<NetworkPage />} />
          <Route path="filters" element={<FiltersPage />} />
          <Route path="validation" element={<ValidationPage />} />
          <Route path="prisma" element={<PrismaPage />} />
        </Route>
        <Route path="projects/:projectId/exports" element={<ExportsPage />} />
      </Route>
    </Routes>
  );
}
