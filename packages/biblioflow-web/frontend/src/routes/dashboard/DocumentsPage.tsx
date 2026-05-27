import { useMemo, useState } from "react";

import { DataTable } from "../../components/common/DataTable";
import { EmptyState } from "../../components/common/EmptyState";
import { useDatasetRecords } from "../../api/queries";
import type { BibliographicRecord } from "../../api/types";
import { firstValue, valueToNumber, valueToString } from "./utils";
import { useActiveWorkspace } from "./workspace";

const sortOptions = [
  ["publication_year", "Year"],
  ["title", "Title"],
  ["source_title", "Source"],
  ["cited_by_count", "Citations"],
];

function searchableText(record: BibliographicRecord): string {
  return [
    record.title,
    record.authors,
    record.source_title,
    record.doi,
    record.keywords_all,
  ]
    .map(valueToString)
    .join(" ")
    .toLowerCase();
}

export function DocumentsPage() {
  const { projectId, activeDatasetId } = useActiveWorkspace();
  const records = useDatasetRecords(projectId, activeDatasetId);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState("publication_year");

  const filteredRecords = useMemo(() => {
    const query = search.trim().toLowerCase();
    return (records.data?.data ?? [])
      .filter((record) => !query || searchableText(record).includes(query))
      .sort((left, right) => {
        if (sortKey === "publication_year" || sortKey === "cited_by_count") {
          return valueToNumber(right[sortKey]) - valueToNumber(left[sortKey]);
        }
        return valueToString(left[sortKey]).localeCompare(
          valueToString(right[sortKey]),
        );
      });
  }, [records.data?.data, search, sortKey]);

  if (records.isLoading) {
    return <p>Loading documents…</p>;
  }

  if (records.isError) {
    return (
      <EmptyState title="Document table failed" icon="!">
        <p>{records.error.message}</p>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack">
      <section className="card section-heading">
        <span className="eyebrow">Documents</span>
        <h2>Normalized record browser</h2>
        <p>
          Search the active dataset by title, author, source, DOI, or keyword.
          The table displays the first 50 matching records to keep the interface
          responsive while backend pagination is still planned.
        </p>
      </section>

      <section className="card document-toolbar">
        <label>
          Search records
          <input
            value={search}
            placeholder="Title, author, source, DOI, keyword…"
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
        <label>
          Sort by
          <select
            value={sortKey}
            onChange={(event) => setSortKey(event.target.value)}
          >
            {sortOptions.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <div className="toolbar-count">
          <span>{filteredRecords.length}</span>
          <small>matching records</small>
        </div>
      </section>

      <section className="card">
        <DataTable
          rows={filteredRecords.slice(0, 50)}
          columns={[
            {
              key: "title",
              header: "Title",
              render: (row) =>
                firstValue(row, ["title", "document_title", "article_title"]),
            },
            {
              key: "authors",
              header: "Authors",
              render: (row) => firstValue(row, ["authors"]),
            },
            {
              key: "publication_year",
              header: "Year",
              render: (row) => firstValue(row, ["publication_year", "year"]),
            },
            {
              key: "source_title",
              header: "Source",
              render: (row) =>
                firstValue(row, ["source_title", "journal", "container_title"]),
            },
            {
              key: "doi",
              header: "DOI",
              render: (row) => firstValue(row, ["doi"]),
            },
            {
              key: "cited_by_count",
              header: "Citations",
              render: (row) =>
                firstValue(row, ["cited_by_count", "times_cited"], "0"),
            },
          ]}
          emptyMessage="No documents match the current search."
        />
      </section>

      <section className="three-column-grid">
        <article className="card placeholder-card">
          <span className="eyebrow">Planned</span>
          <h2>Most cited documents</h2>
          <p>Requires citation ranking helpers in the core library.</p>
        </article>
        <article className="card placeholder-card">
          <span className="eyebrow">Planned</span>
          <h2>Cited references</h2>
          <p>Requires reference parsing and cited reference summaries.</p>
        </article>
        <article className="card placeholder-card">
          <span className="eyebrow">Planned</span>
          <h2>Trend topics</h2>
          <p>Requires topic extraction over publication years.</p>
        </article>
      </section>
    </div>
  );
}
