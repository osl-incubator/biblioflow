import { Link } from "react-router-dom";

import { BarList } from "../../components/common/BarList";
import { DataTable } from "../../components/common/DataTable";
import { EmptyState } from "../../components/common/EmptyState";
import { useDatasetSummary, useOverviewAnalysis } from "../../api/queries";
import { rowsToBars, valueToString } from "./utils";
import { useActiveWorkspace } from "./workspace";

export function OverviewPage() {
  const { projectId, activeDatasetId } = useActiveWorkspace();
  const summary = useDatasetSummary(projectId, activeDatasetId);
  const overview = useOverviewAnalysis(projectId, activeDatasetId, {
    top_n: 20,
    filters: {},
  });

  const mainRows = Object.entries(
    overview.data?.data.main_information ?? {},
  ).map(([metric, value]) => ({ metric: metric.replaceAll("_", " "), value }));
  const annualRows = overview.data?.data.annual_production ?? [];

  if (overview.isLoading || summary.isLoading) {
    return <p>Computing overview metrics…</p>;
  }

  if (overview.isError) {
    return (
      <EmptyState title="Overview analysis failed" icon="!">
        <p>{overview.error.message}</p>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack">
      <section className="card section-heading">
        <span className="eyebrow">Overview</span>
        <h2>Main information</h2>
        <p>
          High-level dataset indicators are produced by biblioflow and reused by
          every web workflow. Use filters when you need to preview a narrowed
          subset before interpreting these metrics.
        </p>
      </section>

      <section className="stat-grid">
        <article className="stat-card accent-search">
          <span>Documents</span>
          <strong>{summary.data?.data.documents ?? "—"}</strong>
          <small>records loaded</small>
        </article>
        <article className="stat-card accent-analysis">
          <span>Keywords</span>
          <strong>{summary.data?.data.keywords ?? "—"}</strong>
          <small>author + index terms</small>
        </article>
        <article className="stat-card accent-appraisal">
          <span>DOI coverage</span>
          <strong>{summary.data?.data.documents_with_doi ?? "—"}</strong>
          <small>documents with DOI</small>
        </article>
        <article className="stat-card accent-synthesis">
          <span>Warnings</span>
          <strong>{summary.data?.data.warnings?.length ?? 0}</strong>
          <small>
            <Link to="../validation">review validation</Link>
          </small>
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Main Information</span>
            <h2>Dataset profile</h2>
          </div>
          <DataTable
            rows={mainRows}
            columns={[
              { key: "metric", header: "Metric" },
              {
                key: "value",
                header: "Value",
                render: (row) => valueToString(row.value),
              },
            ]}
          />
        </article>

        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Annual Production</span>
            <h2>Documents per year</h2>
          </div>
          <BarList
            items={rowsToBars(
              annualRows,
              ["publication_year", "year"],
              ["documents", "count"],
            )}
            emptyMessage="No publication years were detected."
          />
        </article>
      </section>

      <section className="three-column-grid">
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Authors</span>
            <h2>Most relevant authors</h2>
          </div>
          <BarList
            items={rowsToBars(
              overview.data?.data.top_authors,
              ["author", "name"],
              ["documents", "count"],
            )}
          />
        </article>
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Sources</span>
            <h2>Most relevant sources</h2>
          </div>
          <BarList
            items={rowsToBars(
              overview.data?.data.top_sources,
              ["source_title", "source", "name"],
              ["documents", "count"],
            )}
          />
        </article>
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Words</span>
            <h2>Most frequent keywords</h2>
          </div>
          <BarList
            items={rowsToBars(
              overview.data?.data.top_keywords,
              ["keyword", "term", "name"],
              ["documents", "count"],
            )}
          />
        </article>
      </section>
    </div>
  );
}
