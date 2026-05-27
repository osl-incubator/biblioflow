import { BarList } from "../../components/common/BarList";
import { DataTable } from "../../components/common/DataTable";
import { EmptyState } from "../../components/common/EmptyState";
import { useOverviewAnalysis } from "../../api/queries";
import { rowsToBars } from "./utils";
import { useActiveWorkspace } from "./workspace";

export function SourcesPage() {
  const { projectId, activeDatasetId } = useActiveWorkspace();
  const overview = useOverviewAnalysis(projectId, activeDatasetId, {
    top_n: 30,
    filters: {},
  });
  const rows = overview.data?.data.top_sources ?? [];

  if (overview.isLoading) {
    return <p>Loading source analysis…</p>;
  }

  if (overview.isError) {
    return (
      <EmptyState title="Source analysis failed" icon="!">
        <p>{overview.error.message}</p>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack">
      <section className="card section-heading">
        <span className="eyebrow">Sources</span>
        <h2>Journals, books, and venues</h2>
        <p>
          The first web implementation uses overview outputs for most relevant
          sources. Dedicated source impact, Bradford law, and source dynamics
          should be added to the biblioflow package before new backend endpoints
          are exposed.
        </p>
      </section>
      <section className="dashboard-grid">
        <article className="card">
          <h2>Most relevant sources</h2>
          <BarList
            items={rowsToBars(
              rows,
              ["source_title", "source", "name"],
              ["documents", "count"],
            )}
          />
        </article>
        <article className="card">
          <h2>Source table</h2>
          <DataTable
            rows={rows}
            columns={[
              { key: "source_title", header: "Source" },
              { key: "documents", header: "Documents" },
            ]}
            emptyMessage="No sources were detected."
          />
        </article>
      </section>
      <section className="three-column-grid">
        <article className="card placeholder-card">
          <span className="eyebrow">Planned</span>
          <h2>Source impact</h2>
          <p>Requires a future biblioflow source_summary/source_impact API.</p>
        </article>
        <article className="card placeholder-card">
          <span className="eyebrow">Planned</span>
          <h2>Bradford zones</h2>
          <p>Requires Bradford law support in the core library.</p>
        </article>
        <article className="card placeholder-card">
          <span className="eyebrow">Planned</span>
          <h2>Source dynamics</h2>
          <p>Requires a year-by-source dynamics function in biblioflow.</p>
        </article>
      </section>
    </div>
  );
}
