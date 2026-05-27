import { FormEvent, useMemo, useState } from "react";

import { DataTable } from "../../components/common/DataTable";
import { EmptyState } from "../../components/common/EmptyState";
import { useFilterOptions, useFilterPreview } from "../../api/queries";
import type { FilterSpec } from "../../api/types";
import { valueToString } from "./utils";
import { useActiveWorkspace } from "./workspace";

function splitList(value: string): string[] | null {
  const values = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  return values.length ? values : null;
}

function parseNumber(value: string): number | null {
  if (!value.trim()) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function OptionCloud({
  label,
  values,
}: {
  label: string;
  values: string[] | number[];
}) {
  return (
    <div className="option-cloud">
      <strong>{label}</strong>
      <div>
        {values.slice(0, 16).map((value) => (
          <span key={String(value)}>{value}</span>
        ))}
        {values.length > 16 && <span>+{values.length - 16} more</span>}
      </div>
    </div>
  );
}

export function FiltersPage() {
  const { projectId, activeDatasetId } = useActiveWorkspace();
  const options = useFilterOptions(projectId, activeDatasetId);
  const preview = useFilterPreview(projectId, activeDatasetId);
  const [yearMin, setYearMin] = useState("");
  const [yearMax, setYearMax] = useState("");
  const [documentTypes, setDocumentTypes] = useState("");
  const [sources, setSources] = useState("");
  const [authors, setAuthors] = useState("");
  const [keywords, setKeywords] = useState("");
  const [countries, setCountries] = useState("");
  const [minCitations, setMinCitations] = useState("");
  const [includeMissingYear, setIncludeMissingYear] = useState(true);

  const spec = useMemo<FilterSpec>(
    () => ({
      year_min: parseNumber(yearMin),
      year_max: parseNumber(yearMax),
      document_types: splitList(documentTypes),
      sources: splitList(sources),
      authors: splitList(authors),
      countries: splitList(countries),
      keywords: splitList(keywords),
      include_missing_year: includeMissingYear,
      min_global_citations: parseNumber(minCitations),
      custom_field_filters: {},
    }),
    [
      authors,
      countries,
      documentTypes,
      includeMissingYear,
      keywords,
      minCitations,
      sources,
      yearMax,
      yearMin,
    ],
  );

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    preview.mutate(spec);
  }

  return (
    <div className="page-stack">
      <section className="card section-heading">
        <span className="eyebrow">Appraisal</span>
        <h2>Filter preview</h2>
        <p>
          Build a filter specification and preview the resulting dataset size.
          This first implementation keeps filter state local to the page.
        </p>
      </section>

      <section className="dashboard-grid">
        <form className="card form-card" onSubmit={onSubmit}>
          <div className="section-heading compact">
            <span className="eyebrow">Controls</span>
            <h2>Refine records</h2>
          </div>
          <div className="form-grid two-columns">
            <label>
              Year minimum
              <input
                type="number"
                value={yearMin}
                placeholder="e.g. 2015"
                onChange={(event) => setYearMin(event.target.value)}
              />
            </label>
            <label>
              Year maximum
              <input
                type="number"
                value={yearMax}
                placeholder="e.g. 2026"
                onChange={(event) => setYearMax(event.target.value)}
              />
            </label>
            <label>
              Document types
              <input
                value={documentTypes}
                placeholder="article, review"
                onChange={(event) => setDocumentTypes(event.target.value)}
              />
            </label>
            <label>
              Minimum citations
              <input
                type="number"
                min="0"
                value={minCitations}
                placeholder="0"
                onChange={(event) => setMinCitations(event.target.value)}
              />
            </label>
          </div>
          <label>
            Sources
            <input
              value={sources}
              placeholder="Comma-separated source titles"
              onChange={(event) => setSources(event.target.value)}
            />
          </label>
          <label>
            Authors
            <input
              value={authors}
              placeholder="Comma-separated author names"
              onChange={(event) => setAuthors(event.target.value)}
            />
          </label>
          <label>
            Keywords
            <input
              value={keywords}
              placeholder="Comma-separated keywords"
              onChange={(event) => setKeywords(event.target.value)}
            />
          </label>
          <label>
            Countries
            <input
              value={countries}
              placeholder="Comma-separated countries"
              onChange={(event) => setCountries(event.target.value)}
            />
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={includeMissingYear}
              onChange={(event) => setIncludeMissingYear(event.target.checked)}
            />
            Include records with missing publication year
          </label>
          <button
            type="submit"
            className="button-primary"
            disabled={preview.isPending}
          >
            {preview.isPending ? "Previewing…" : "Preview filters"}
          </button>
          {preview.isError && <p role="alert">{preview.error.message}</p>}
        </form>

        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Available values</span>
            <h2>Dataset facets</h2>
          </div>
          {options.isLoading && <p>Loading filter options…</p>}
          {options.isError && (
            <p role="alert">Unable to load filter options.</p>
          )}
          {options.data && (
            <div className="option-cloud-list">
              <OptionCloud label="Years" values={options.data.data.years} />
              <OptionCloud
                label="Document types"
                values={options.data.data.document_types}
              />
              <OptionCloud label="Sources" values={options.data.data.sources} />
              <OptionCloud label="Authors" values={options.data.data.authors} />
              <OptionCloud
                label="Keywords"
                values={options.data.data.keywords}
              />
            </div>
          )}
        </article>
      </section>

      <section className="card">
        <div className="section-heading compact">
          <span className="eyebrow">Preview result</span>
          <h2>Filter impact</h2>
        </div>
        {preview.data ? (
          <>
            <div className="stat-grid compact-stats">
              <article className="stat-card">
                <span>Input</span>
                <strong>{preview.data.data.input_records}</strong>
                <small>records</small>
              </article>
              <article className="stat-card">
                <span>Output</span>
                <strong>{preview.data.data.output_records}</strong>
                <small>records</small>
              </article>
              <article className="stat-card">
                <span>Reduction</span>
                <strong>
                  {preview.data.data.input_records
                    ? `${Math.round(
                        (1 -
                          preview.data.data.output_records /
                            preview.data.data.input_records) *
                          100,
                      )}%`
                    : "0%"}
                </strong>
                <small>records removed</small>
              </article>
              <article className="stat-card">
                <span>Keywords</span>
                <strong>{preview.data.data.summary.keywords}</strong>
                <small>after filtering</small>
              </article>
            </div>
            <DataTable
              rows={Object.entries(preview.data.data.spec).map(
                ([key, value]) => ({
                  key,
                  value,
                }),
              )}
              columns={[
                { key: "key", header: "Filter" },
                {
                  key: "value",
                  header: "Value",
                  render: (row) => valueToString(row.value),
                },
              ]}
            />
          </>
        ) : (
          <EmptyState title="No filter preview yet" icon="◇">
            <p>Submit the controls above to see how many records remain.</p>
          </EmptyState>
        )}
      </section>
    </div>
  );
}
