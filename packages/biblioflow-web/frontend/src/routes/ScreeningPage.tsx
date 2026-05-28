import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { DataTable } from "../components/common/DataTable";
import { EmptyState } from "../components/common/EmptyState";
import {
  useProject,
  usePromoteScreeningCandidates,
  useScreeningRun,
  useScreeningRuns,
  useUpdateScreeningCandidates,
} from "../api/queries";
import type { ScreeningCandidate } from "../api/types";

function candidateMatches(
  candidate: ScreeningCandidate,
  query: string,
): boolean {
  const normalized = query.trim().toLowerCase();
  if (!normalized) {
    return true;
  }
  const searchable = [
    candidate.title,
    candidate.year?.toString() ?? "",
    candidate.source_title ?? "",
    candidate.status,
    candidate.authors.join(" "),
    Object.values(candidate.identifiers).join(" "),
  ]
    .join(" ")
    .toLowerCase();
  return searchable.includes(normalized);
}

function identifiersText(candidate: ScreeningCandidate): string {
  const entries = Object.entries(candidate.identifiers);
  if (!entries.length) {
    return "—";
  }
  return entries
    .map(([key, value]) => `${key.toUpperCase()}: ${value}`)
    .join(" · ");
}

function isImportable(status: string): boolean {
  return !["excluded", "duplicate", "imported", "error"].includes(status);
}

export function ScreeningPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedRunId = searchParams.get("run");
  const project = useProject(projectId);
  const screeningRuns = useScreeningRuns(projectId);
  const [activeScreeningRunId, setActiveScreeningRunId] = useState<
    string | null
  >(requestedRunId);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>(
    [],
  );
  const [candidateFilter, setCandidateFilter] = useState("");
  const [promoteName, setPromoteName] = useState("");
  const screeningRun = useScreeningRun(projectId, activeScreeningRunId);
  const updateScreeningCandidates = useUpdateScreeningCandidates(
    projectId,
    activeScreeningRunId,
  );
  const promoteScreeningCandidates = usePromoteScreeningCandidates(
    projectId,
    activeScreeningRunId,
  );
  const stagedRun = screeningRun.data?.data ?? null;
  const visibleCandidates =
    stagedRun?.candidates.filter((candidate) =>
      candidateMatches(candidate, candidateFilter),
    ) ?? [];
  const promotableVisibleCandidateIds = visibleCandidates
    .filter((candidate) => isImportable(candidate.status))
    .map((candidate) => candidate.candidate_id);
  const selectedVisibleCount = visibleCandidates.filter((candidate) =>
    selectedCandidateIds.includes(candidate.candidate_id),
  ).length;

  useEffect(() => {
    setActiveScreeningRunId(requestedRunId);
  }, [requestedRunId]);

  useEffect(() => {
    if (!activeScreeningRunId && screeningRuns.data?.data.length) {
      const latestRun = screeningRuns.data.data.at(-1);
      if (latestRun) {
        setActiveScreeningRunId(latestRun.screening_run_id);
        setSearchParams({ run: latestRun.screening_run_id });
      }
    }
  }, [activeScreeningRunId, screeningRuns.data?.data, setSearchParams]);

  useEffect(() => {
    if (stagedRun?.screening_run_id === activeScreeningRunId) {
      setPromoteName(stagedRun.name);
      setSelectedCandidateIds(
        stagedRun.candidates
          .filter((candidate) => isImportable(candidate.status))
          .map((candidate) => candidate.candidate_id),
      );
    }
  }, [activeScreeningRunId, stagedRun?.screening_run_id]);

  function activateRun(screeningRunId: string) {
    setActiveScreeningRunId(screeningRunId);
    setSearchParams({ run: screeningRunId });
    setSelectedCandidateIds([]);
    setCandidateFilter("");
    promoteScreeningCandidates.reset();
    updateScreeningCandidates.reset();
  }

  function toggleCandidate(candidateId: string) {
    setSelectedCandidateIds((current) =>
      current.includes(candidateId)
        ? current.filter((item) => item !== candidateId)
        : [...current, candidateId],
    );
  }

  function selectVisibleCandidates() {
    setSelectedCandidateIds((current) => [
      ...new Set([...current, ...promotableVisibleCandidateIds]),
    ]);
  }

  function clearVisibleCandidates() {
    setSelectedCandidateIds((current) =>
      current.filter(
        (candidateId) => !promotableVisibleCandidateIds.includes(candidateId),
      ),
    );
  }

  function applyCandidateDecision(
    status: "candidate" | "selected" | "maybe" | "excluded" | "duplicate",
  ) {
    updateScreeningCandidates.mutate(
      { candidate_ids: selectedCandidateIds, status },
      {
        onSuccess: () => {
          if (["excluded", "duplicate"].includes(status)) {
            setSelectedCandidateIds([]);
          }
        },
      },
    );
  }

  function promoteSelectedCandidates() {
    promoteScreeningCandidates.mutate(
      {
        candidate_ids: selectedCandidateIds,
        name: promoteName.trim() || null,
      },
      {
        onSuccess: () => setSelectedCandidateIds([]),
      },
    );
  }

  if (project.isLoading) {
    return <p>Loading project…</p>;
  }

  if (project.isError || !projectId) {
    return (
      <EmptyState title="Project not found" icon="!">
        <p>Select or create a project before screening records.</p>
        <Link className="button button-primary" to="/projects">
          Back to projects
        </Link>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack">
      <section className="dashboard-hero card">
        <div>
          <span className="eyebrow">Appraisal</span>
          <h1>Screening</h1>
          <p>
            Review staged records from uploads and remote searches before they
            become an active analysis dataset.
          </p>
        </div>
        <div className="section-actions">
          <Link
            className="button button-secondary"
            to={`/projects/${projectId}/upload`}
          >
            Import records
          </Link>
          <Link
            className="button button-secondary"
            to={`/projects/${projectId}/dashboard/overview`}
          >
            Go to dashboard
          </Link>
        </div>
      </section>

      <section className="dashboard-grid">
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Screening runs</span>
            <h2>Staged imports</h2>
          </div>
          {screeningRuns.isLoading && <p>Loading screening runs…</p>}
          {screeningRuns.isError && (
            <p role="alert">Unable to load screening runs.</p>
          )}
          {screeningRuns.data?.data.length ? (
            <div className="remote-search-list">
              {screeningRuns.data.data.map((run) => (
                <button
                  key={run.screening_run_id}
                  type="button"
                  className={
                    run.screening_run_id === activeScreeningRunId
                      ? "chip-button active"
                      : "chip-button"
                  }
                  onClick={() => activateRun(run.screening_run_id)}
                >
                  {run.name} · {run.records} records
                </button>
              ))}
            </div>
          ) : (
            !screeningRuns.isLoading && (
              <EmptyState title="No screening runs" icon="◆">
                <p>
                  Stage uploaded files or remote source results before reviewing
                  records here.
                </p>
                <Link
                  className="button button-primary"
                  to={`/projects/${projectId}/upload`}
                >
                  Import records
                </Link>
              </EmptyState>
            )
          )}
        </article>

        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Promotion</span>
            <h2>Create dataset</h2>
          </div>
          <p className="muted-copy">
            Select candidates in the queue, then promote them into the project
            active dataset. Excluded, duplicate, imported, and error records are
            never selected by default.
          </p>
          <label>
            Dataset name
            <input
              placeholder="Optional"
              value={promoteName}
              onChange={(event) => setPromoteName(event.target.value)}
            />
          </label>
        </article>
      </section>

      {screeningRun.isLoading && activeScreeningRunId && (
        <p>Loading screening candidates…</p>
      )}
      {!activeScreeningRunId && !screeningRuns.isLoading && (
        <EmptyState title="Select a screening run" icon="◆">
          <p>Choose a staged import to review its candidates.</p>
        </EmptyState>
      )}
      {stagedRun && (
        <div
          className="screening-panel card"
          role="region"
          aria-label="Screening candidates"
        >
          <div className="screening-summary">
            <div>
              <span className="eyebrow">Screening queue</span>
              <h2>{stagedRun.name}</h2>
              <p className="muted-copy">
                {stagedRun.candidates.length} candidates staged from{" "}
                {stagedRun.source_label}. Select records to promote into the
                active dataset, or mark obvious misses as excluded.
              </p>
            </div>
            <div
              className="screening-counts"
              aria-label="Candidate status counts"
            >
              {Object.entries(stagedRun.status_counts ?? {}).map(
                ([status, count]) => (
                  <span className={`status-pill ${status}`} key={status}>
                    {status}: {String(count)}
                  </span>
                ),
              )}
            </div>
          </div>
          <div className="screening-toolbar">
            <label>
              Filter candidates
              <input
                placeholder="Title, author, PMID, DOI, journal…"
                value={candidateFilter}
                onChange={(event) => setCandidateFilter(event.target.value)}
              />
            </label>
            <div className="section-actions">
              <button type="button" onClick={selectVisibleCandidates}>
                Select visible
              </button>
              <button
                type="button"
                className="button-secondary"
                onClick={clearVisibleCandidates}
              >
                Clear visible
              </button>
            </div>
          </div>
          <p className="muted-copy">
            Selected {selectedCandidateIds.length} records (
            {selectedVisibleCount} visible).
          </p>
          <DataTable
            rows={visibleCandidates}
            columns={[
              {
                key: "candidate_id",
                header: "Keep",
                render: (row) => (
                  <input
                    type="checkbox"
                    aria-label={`Select ${row.title}`}
                    checked={selectedCandidateIds.includes(row.candidate_id)}
                    disabled={!isImportable(row.status)}
                    onChange={() => toggleCandidate(row.candidate_id)}
                  />
                ),
              },
              {
                key: "status",
                header: "Status",
                render: (row) => (
                  <span className={`status-pill ${row.status}`}>
                    {row.status}
                  </span>
                ),
              },
              { key: "title", header: "Title" },
              {
                key: "authors",
                header: "Authors",
                render: (row) => row.authors.join("; ") || "—",
              },
              {
                key: "year",
                header: "Year",
                render: (row) => row.year ?? "—",
              },
              {
                key: "source_title",
                header: "Source",
                render: (row) => row.source_title ?? "—",
              },
              {
                key: "identifiers",
                header: "Identifiers",
                render: (row) => identifiersText(row),
              },
            ]}
          />
          <div className="section-actions screening-actions">
            <button
              type="button"
              onClick={() => applyCandidateDecision("selected")}
              disabled={
                !selectedCandidateIds.length ||
                updateScreeningCandidates.isPending
              }
            >
              Mark selected as keep
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={() => applyCandidateDecision("excluded")}
              disabled={
                !selectedCandidateIds.length ||
                updateScreeningCandidates.isPending
              }
            >
              Exclude selected
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={() => applyCandidateDecision("maybe")}
              disabled={
                !selectedCandidateIds.length ||
                updateScreeningCandidates.isPending
              }
            >
              Mark as maybe
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={() => applyCandidateDecision("duplicate")}
              disabled={
                !selectedCandidateIds.length ||
                updateScreeningCandidates.isPending
              }
            >
              Mark duplicate
            </button>
            <button
              type="button"
              className="button-primary"
              onClick={promoteSelectedCandidates}
              disabled={
                !selectedCandidateIds.length ||
                promoteScreeningCandidates.isPending
              }
            >
              {promoteScreeningCandidates.isPending
                ? "Creating dataset…"
                : "Create dataset from selected"}
            </button>
          </div>
          {updateScreeningCandidates.isError && (
            <p role="alert">{updateScreeningCandidates.error.message}</p>
          )}
          {promoteScreeningCandidates.isError && (
            <p role="alert">{promoteScreeningCandidates.error.message}</p>
          )}
        </div>
      )}
      {promoteScreeningCandidates.data?.data && (
        <div className="success-callout" role="status">
          Created dataset{" "}
          <code>{promoteScreeningCandidates.data.data.dataset_id}</code> from{" "}
          <strong>{promoteScreeningCandidates.data.data.records.length}</strong>{" "}
          screened records.
          <Link
            className="button button-secondary"
            to={`/projects/${projectId}/dashboard/overview`}
          >
            Go to dashboard
          </Link>
        </div>
      )}
    </div>
  );
}
