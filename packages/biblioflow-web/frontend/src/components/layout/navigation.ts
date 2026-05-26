export type NavigationAccent =
  | "search"
  | "appraisal"
  | "analysis"
  | "synthesis";

export interface NavigationItem {
  label: string;
  detail?: string;
  disabled?: boolean;
  buildPath?: (projectId: string) => string;
  fallbackPath?: string;
  requiresProject?: boolean;
}

export interface NavigationSection {
  label: string;
  accent: NavigationAccent;
  icon: string;
  items: NavigationItem[];
}

export function dashboardPath(projectId: string, section: string): string {
  return `/projects/${projectId}/dashboard/${section}`;
}

export const navigationSections: NavigationSection[] = [
  {
    label: "Search",
    accent: "search",
    icon: "⌕",
    items: [
      {
        label: "Import or Load",
        detail: "Files and APIs",
        buildPath: (projectId) => `/projects/${projectId}/upload`,
        fallbackPath: "/projects",
        requiresProject: false,
      },
      { label: "OpenAlex", detail: "API connector planned", disabled: true },
      { label: "PubMed", detail: "API connector planned", disabled: true },
      { label: "Merge Collections", detail: "Coming soon", disabled: true },
      { label: "Reference Matching", detail: "Coming soon", disabled: true },
    ],
  },
  {
    label: "Appraisal",
    accent: "appraisal",
    icon: "◆",
    items: [
      {
        label: "Filters",
        detail: "Refine dataset",
        buildPath: (projectId) => dashboardPath(projectId, "filters"),
        fallbackPath: "/projects",
      },
      {
        label: "Validation",
        detail: "Warnings",
        buildPath: (projectId) => dashboardPath(projectId, "validation"),
        fallbackPath: "/projects",
      },
      { label: "PRISMA Diagram", detail: "Planned", disabled: true },
    ],
  },
  {
    label: "Analysis",
    accent: "analysis",
    icon: "↗",
    items: [
      {
        label: "Overview",
        detail: "Main information",
        buildPath: (projectId) => dashboardPath(projectId, "overview"),
        fallbackPath: "/projects",
      },
      {
        label: "Sources",
        detail: "Journals",
        buildPath: (projectId) => dashboardPath(projectId, "sources"),
        fallbackPath: "/projects",
      },
      {
        label: "Authors",
        detail: "People and affiliations",
        buildPath: (projectId) => dashboardPath(projectId, "authors"),
        fallbackPath: "/projects",
      },
      {
        label: "Documents",
        detail: "Papers and references",
        buildPath: (projectId) => dashboardPath(projectId, "documents"),
        fallbackPath: "/projects",
      },
      {
        label: "Words",
        detail: "Keywords and terms",
        buildPath: (projectId) => dashboardPath(projectId, "words"),
        fallbackPath: "/projects",
      },
    ],
  },
  {
    label: "Synthesis",
    accent: "synthesis",
    icon: "✦",
    items: [
      {
        label: "Conceptual Structure",
        detail: "Co-word maps",
        buildPath: (projectId) =>
          dashboardPath(projectId, "conceptual-structure"),
        fallbackPath: "/projects",
      },
      {
        label: "Intellectual Structure",
        detail: "Citations",
        buildPath: (projectId) =>
          dashboardPath(projectId, "intellectual-structure"),
        fallbackPath: "/projects",
      },
      {
        label: "Social Structure",
        detail: "Collaboration",
        buildPath: (projectId) => dashboardPath(projectId, "social-structure"),
        fallbackPath: "/projects",
      },
      {
        label: "Matrices",
        detail: "Adjacency tables",
        buildPath: (projectId) => dashboardPath(projectId, "matrices"),
        fallbackPath: "/projects",
      },
      {
        label: "Networks",
        detail: "Nodes and edges",
        buildPath: (projectId) => dashboardPath(projectId, "networks"),
        fallbackPath: "/projects",
      },
      { label: "Report", detail: "Narrative export planned", disabled: true },
      {
        label: "Export",
        detail: "Artifacts",
        buildPath: (projectId) => `/projects/${projectId}/exports`,
        fallbackPath: "/projects",
      },
    ],
  },
];
