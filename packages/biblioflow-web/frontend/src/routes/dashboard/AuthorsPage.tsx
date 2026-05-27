import { BarList } from "../../components/common/BarList";
import { DataTable } from "../../components/common/DataTable";
import { EmptyState } from "../../components/common/EmptyState";
import { useOverviewAnalysis } from "../../api/queries";
import { rowsToBars } from "./utils";
import { useActiveWorkspace } from "./workspace";

export function AuthorsPage() {
  const { projectId, activeDatasetId } = useActiveWorkspace();
  const overview = useOverviewAnalysis(projectId, activeDatasetId, {
    top_n: 30,
    filters: {},
  });
  const rows = overview.data?.data.top_authors ?? [];

  if (overview.isLoading) {
    return <p>Loading author analysis…</p>;
  }

  if (overview.isError) {
    return (
      <EmptyState title="Author analysis failed" icon="!">
        <p>{overview.error.message}</p>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack">
      <section className="card section-heading">
        <span className="eyebrow">Authors</span>
        <h2>People, affiliations, and countries</h2>
        <p>
          Author counts are available from the overview endpoint. Author
          productivity over time, affiliations, country analysis, and Lotka law
          should be implemented in biblioflow before richer panels are wired.
        </p>
      </section>
      <section className="dashboard-grid">
        <article className="card">
          <h2>Most relevant authors</h2>
          <BarList
            items={rowsToBars(rows, ["author", "name"], ["documents", "count"])}
          />
        </article>
        <article className="card">
          <h2>Author table</h2>
          <DataTable
            rows={rows}
            columns={[
              { key: "author", header: "Author" },
              { key: "documents", header: "Documents" },
            ]}
            emptyMessage="No authors were detected."
          />
        </article>
      </section>
      <section className="three-column-grid">
        <article className="card placeholder-card">
          <span className="eyebrow">Planned</span>
          <h2>Production over time</h2>
          <p>Requires an author_productivity function in biblioflow.</p>
        </article>
        <article className="card placeholder-card">
          <span className="eyebrow">Planned</span>
          <h2>Affiliations</h2>
          <p>Requires affiliation normalization and summary support.</p>
        </article>
        <article className="card placeholder-card">
          <span className="eyebrow">Planned</span>
          <h2>Countries</h2>
          <p>Requires country extraction/summary in the core library.</p>
        </article>
      </section>
    </div>
  );
}
