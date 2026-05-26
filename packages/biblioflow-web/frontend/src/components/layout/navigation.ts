export interface NavigationItem {
  label: string;
  detail?: string;
  path?: string;
  disabled?: boolean;
}

export interface NavigationSection {
  label: string;
  accent: "search" | "appraisal" | "analysis" | "synthesis";
  icon: string;
  items: NavigationItem[];
}

export const navigationSections: NavigationSection[] = [
  {
    label: "Search",
    accent: "search",
    icon: "⌕",
    items: [
      { label: "Import or Load", detail: "Files and APIs", path: "/projects" },
      { label: "OpenAlex", detail: "API", disabled: true },
      { label: "PubMed", detail: "API", disabled: true },
      { label: "Merge Collections", detail: "Coming soon", disabled: true },
      { label: "Reference Matching", detail: "Coming soon", disabled: true },
    ],
  },
  {
    label: "Appraisal",
    accent: "appraisal",
    icon: "◆",
    items: [
      { label: "Filters", detail: "Refine dataset", path: "/projects" },
      { label: "Validation", detail: "Warnings", path: "/projects" },
      { label: "PRISMA Diagram", detail: "Planned", disabled: true },
    ],
  },
  {
    label: "Analysis",
    accent: "analysis",
    icon: "↗",
    items: [
      { label: "Overview", detail: "Main information", path: "/projects" },
      { label: "Sources", detail: "Journals", path: "/projects" },
      {
        label: "Authors",
        detail: "People and affiliations",
        path: "/projects",
      },
      {
        label: "Documents",
        detail: "Papers and references",
        path: "/projects",
      },
      { label: "Words", detail: "Keywords and terms", path: "/projects" },
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
        path: "/projects",
      },
      {
        label: "Intellectual Structure",
        detail: "Citations",
        path: "/projects",
      },
      {
        label: "Social Structure",
        detail: "Collaboration",
        path: "/projects",
      },
      { label: "Report", detail: "Narrative export", disabled: true },
      { label: "TALL Export", detail: "Artifacts", path: "/projects" },
    ],
  },
];
