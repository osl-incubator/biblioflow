import { BarList } from "../../components/common/BarList";
import { DataTable } from "../../components/common/DataTable";
import { EmptyState } from "../../components/common/EmptyState";
import { useOverviewAnalysis } from "../../api/queries";
import { rowsToBars } from "./utils";
import { useActiveWorkspace } from "./workspace";

export function WordsPage() {
  const { projectId, activeDatasetId } = useActiveWorkspace();
  const overview = useOverviewAnalysis(projectId, activeDatasetId, {
    top_n: 40,
    filters: {},
  });
  const rows = overview.data?.data.top_keywords ?? [];

  if (overview.isLoading) {
    return <p>Loading word analysis…</p>;
  }

  if (overview.isError) {
    return (
      <EmptyState title="Word analysis failed" icon="!">
        <p>{overview.error.message}</p>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack">
      <section className="card section-heading">
        <span className="eyebrow">Words</span>
        <h2>Keywords and terms</h2>
        <p>
          Use keyword frequencies to decide whether a conceptual matrix or
          network should be generated from author keywords, index keywords, or
          combined normalized terms.
        </p>
      </section>
      <section className="dashboard-grid">
        <article className="card">
          <h2>Most frequent keywords</h2>
          <BarList
            items={rowsToBars(
              rows,
              ["keyword", "term", "name"],
              ["documents", "count"],
            )}
          />
        </article>
        <article className="card">
          <h2>Keyword table</h2>
          <DataTable
            rows={rows}
            columns={[
              { key: "keyword", header: "Keyword" },
              { key: "documents", header: "Documents" },
            ]}
            emptyMessage="No keywords were detected."
          />
        </article>
      </section>
      <section className="three-column-grid">
        <article className="card placeholder-card">
          <span className="eyebrow">Next</span>
          <h2>Trend topics</h2>
          <p>Requires term-by-year summaries in biblioflow.</p>
        </article>
        <article className="card placeholder-card">
          <span className="eyebrow">Next</span>
          <h2>Thematic map</h2>
          <p>Requires clustering metrics and thematic quadrant helpers.</p>
        </article>
        <article className="card placeholder-card">
          <span className="eyebrow">Available</span>
          <h2>Co-word network</h2>
          <p>
            Use the Networks page with kind co_occurrence and unit keywords_all.
          </p>
        </article>
      </section>
    </div>
  );
}
