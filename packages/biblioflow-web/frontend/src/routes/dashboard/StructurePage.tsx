import { Link } from "react-router-dom";

import { EmptyState } from "../../components/common/EmptyState";
import { useActiveWorkspace } from "./workspace";

type StructureKind = "conceptual" | "intellectual" | "social";

interface StructurePageProps {
  kind: StructureKind;
}

const copy: Record<
  StructureKind,
  {
    title: string;
    subtitle: string;
    matrix: string;
    network: string;
    bullets: string[];
  }
> = {
  conceptual: {
    title: "Conceptual structure",
    subtitle: "Explore themes using keyword and term co-occurrence.",
    matrix: "co_occurrence / keywords_all",
    network: "Keyword co-word network",
    bullets: [
      "Start with the Words page to inspect top terms.",
      "Build a co-occurrence matrix with unit keywords_all.",
      "Use association normalization when comparing term pairs.",
    ],
  },
  intellectual: {
    title: "Intellectual structure",
    subtitle: "Inspect citation relationships and shared reference patterns.",
    matrix: "co_citation or bibliographic_coupling / references",
    network: "Citation structure network",
    bullets: [
      "Use co-citation when reference lists are available.",
      "Use bibliographic coupling for shared references between documents.",
      "Use direct citation when records contain resolvable references.",
    ],
  },
  social: {
    title: "Social structure",
    subtitle: "Map collaboration between authors, affiliations, or countries.",
    matrix: "collaboration / authors",
    network: "Collaboration network",
    bullets: [
      "Start with author collaboration to inspect co-authorship.",
      "Use country or affiliation units after those fields are normalized.",
      "Raise minimum occurrences to reduce low-signal links.",
    ],
  },
};

export function StructurePage({ kind }: StructurePageProps) {
  const { projectId } = useActiveWorkspace();
  const details = copy[kind];

  if (!projectId) {
    return (
      <EmptyState title="Project required" icon="!">
        <p>Select a project before opening structure workflows.</p>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack">
      <section className="card section-heading">
        <span className="eyebrow">Synthesis</span>
        <h2>{details.title}</h2>
        <p>{details.subtitle}</p>
      </section>

      <section className="dashboard-grid">
        <article className="card structure-card">
          <span className="eyebrow">Recommended matrix</span>
          <h2>{details.matrix}</h2>
          <p>
            Generate the table first, then decide whether a node/edge network is
            appropriate for interpretation or export.
          </p>
          <Link
            className="button button-primary"
            to={`/projects/${projectId}/dashboard/matrices`}
          >
            Open matrices
          </Link>
        </article>
        <article className="card structure-card">
          <span className="eyebrow">Recommended network</span>
          <h2>{details.network}</h2>
          <p>
            Build the network from biblioflow and review node/edge tables before
            adding visual graph layouts in a later iteration.
          </p>
          <Link
            className="button button-secondary"
            to={`/projects/${projectId}/dashboard/networks`}
          >
            Open networks
          </Link>
        </article>
      </section>

      <section className="card">
        <span className="eyebrow">Workflow checklist</span>
        <h2>Suggested interpretation path</h2>
        <ul className="guidance-list">
          {details.bullets.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
