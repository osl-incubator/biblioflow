import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

import { DataTable } from "../components/common/DataTable";
import { EmptyState } from "../components/common/EmptyState";
import {
  useProject,
  usePromoteScreeningCandidates,
  useScreeningCandidates,
  useScreeningRun,
  useScreeningRuns,
  useUpdateAllScreeningCandidates,
  useUpdateScreeningCandidates,
} from "../api/queries";
import type {
  ScreeningCandidate,
  ScreeningCandidateAggregateItem,
} from "../api/types";

type ScreeningCandidateRow = ScreeningCandidate &
  Partial<ScreeningCandidateAggregateItem>;

type ScreeningView = "run" | "all";

function candidateMatches(
  candidate: ScreeningCandidateRow,
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
    candidate.screening_run_name ?? "",
    candidate.source_label ?? "",
    candidate.duplicate_match_basis ?? "",
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

function duplicateLabel(candidate: ScreeningCandidateAggregateItem): string {
  if (!candidate.duplicate_group_id || candidate.duplicate_group_size < 2) {
    return "—";
  }
  return `${candidate.duplicate_match_basis ?? "match"} · ${
    candidate.duplicate_group_size
  } records`;
}

export function ScreeningPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedRunId = searchParams.get("run");
  const requestedView: ScreeningView =
    searchParams.get("view") === "all" ? "all" : "run";
  const project = useProject(projectId);
  const screeningRuns = useScreeningRuns(projectId);
  const allStagedCandidates = useScreeningCandidates(projectId);
  const [screeningView, setScreeningView] =
    useState<ScreeningView>(requestedView);
  const [activeScreeningRunId, setActiveScreeningRunId] = useState<
    string | null
  >(requestedView === "all" ? null : requestedRunId);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>(
    [],
  );
  const [selectedAllCandidateIds, setSelectedAllCandidateIds] = useState<
    string[]
  >([]);
  const [candidateFilter, setCandidateFilter] = useState("");
  const [promoteName, setPromoteName] = useState("");
  const screeningRun = useScreeningRun(
    projectId,
    screeningView === "all" ? null : activeScreeningRunId,
  );
  const updateScreeningCandidates = useUpdateScreeningCandidates(
    projectId,
    activeScreeningRunId,
  );
  const updateAllScreeningCandidates =
    useUpdateAllScreeningCandidates(projectId);
  const promoteScreeningCandidates = usePromoteScreeningCandidates(
    projectId,
    activeScreeningRunId,
  );
  const stagedRun = screeningRun.data?.data ?? null;
  const allStaged =
    updateAllScreeningCandidates.data?.data ??
    allStagedCandidates.data?.data ??
    null;
  const allStagedRecordCount =
    allStaged?.records ??
    screeningRuns.data?.data.reduce((total, run) => total + run.records, 0) ??
    0;
  const visibleAllCandidates =
    allStaged?.candidates.filter((candidate) =>
      candidateMatches(candidate, candidateFilter),
    ) ?? [];
  const promotableVisibleAllCandidateIds = visibleAllCandidates
    .filter((candidate) => isImportable(candidate.status))
    .map((candidate) => candidate.id);
  const selectedAllVisibleCount = visibleAllCandidates.filter((candidate) =>
    selectedAllCandidateIds.includes(candidate.id),
  ).length;
  const duplicateGroups = allStaged?.duplicate_groups ?? [];
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
    setScreeningView(requestedView);
    setActiveScreeningRunId(requestedView === "all" ? null : requestedRunId);
  }, [requestedRunId, requestedView]);

  useEffect(() => {
    if (
      screeningView === "run" &&
      !activeScreeningRunId &&
      screeningRuns.data?.data.length
    ) {
      const latestRun = screeningRuns.data.data.at(-1);
      if (latestRun) {
        setActiveScreeningRunId(latestRun.screening_run_id);
        setSearchParams({ run: latestRun.screening_run_id });
      }
    }
  }, [
    activeScreeningRunId,
    screeningRuns.data?.data,
    screeningView,
    setSearchParams,
  ]);

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
    setScreeningView("run");
    setActiveScreeningRunId(screeningRunId);
    setSearchParams({ run: screeningRunId });
    setSelectedCandidateIds([]);
    setSelectedAllCandidateIds([]);
    setCandidateFilter("");
    promoteScreeningCandidates.reset();
    updateAllScreeningCandidates.reset();
    updateScreeningCandidates.reset();
  }

  function activateAllStagedRecords() {
    setScreeningView("all");
    setActiveScreeningRunId(null);
    setSearchParams({ view: "all" });
    setSelectedCandidateIds([]);
    setSelectedAllCandidateIds([]);
    setCandidateFilter("");
    promoteScreeningCandidates.reset();
    updateAllScreeningCandidates.reset();
    updateScreeningCandidates.reset();
  }

  function toggleCandidate(candidateId: string) {
    setSelectedCandidateIds((current) =>
      current.includes(candidateId)
        ? current.filter((item) => item !== candidateId)
        : [...current, candidateId],
    );
  }

  function toggleAllCandidate(candidateId: string) {
    setSelectedAllCandidateIds((current) =>
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

  function selectVisibleAllCandidates() {
    setSelectedAllCandidateIds((current) => [
      ...new Set([...current, ...promotableVisibleAllCandidateIds]),
    ]);
  }

  function clearVisibleCandidates() {
    setSelectedCandidateIds((current) =>
      current.filter(
        (candidateId) => !promotableVisibleCandidateIds.includes(candidateId),
      ),
    );
  }

  function clearVisibleAllCandidates() {
    setSelectedAllCandidateIds((current) =>
      current.filter(
        (candidateId) =>
          !promotableVisibleAllCandidateIds.includes(candidateId),
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

  function applyAllCandidateDecision(
    status: "candidate" | "selected" | "maybe" | "excluded" | "duplicate",
  ) {
    const selectedCandidates = (allStaged?.candidates ?? []).filter(
      (candidate) => selectedAllCandidateIds.includes(candidate.id),
    );
    updateAllScreeningCandidates.mutate({
      candidates: selectedCandidates.map((candidate) => ({
        screening_run_id: candidate.screening_run_id,
        candidate_id: candidate.candidate_id,
      })),
      status,
    });
    if (["excluded", "duplicate"].includes(status)) {
      setSelectedAllCandidateIds([]);
    }
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
            Go to Import page
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
              <button
                type="button"
                className={
                  screeningView === "all" ? "chip-button active" : "chip-button"
                }
                onClick={activateAllStagedRecords}
              >
                All staged records · {allStagedRecordCount} records
                {duplicateGroups.length
                  ? ` · ${duplicateGroups.length} duplicate groups`
                  : ""}
              </button>
              {screeningRuns.data.data.map((run) => (
                <button
                  key={run.screening_run_id}
                  type="button"
                  className={
                    screeningView === "run" &&
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
              <EmptyState title="No staged records to screen" icon="◆">
                <p>
                  Screening reviews records that were already staged from an
                  uploaded file or API search. Use the Import page to upload
                  files or run source searches first.
                </p>
                <Link
                  className="button button-secondary"
                  to={`/projects/${projectId}/upload`}
                >
                  Go to Import page
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

      {screeningRun.isLoading &&
        screeningView === "run" &&
        activeScreeningRunId && <p>Loading screening candidates…</p>}
      {screeningView === "all" && allStagedCandidates.isLoading && (
        <p>Loading all staged records…</p>
      )}
      {screeningView === "run" &&
        !activeScreeningRunId &&
        !screeningRuns.isLoading && (
          <EmptyState title="Select a screening run" icon="◆">
            <p>
              Choose a staged import from the list above to review its
              candidates.
            </p>
          </EmptyState>
        )}
      {screeningView === "all" && allStaged && (
        <div
          className="screening-panel card"
          role="region"
          aria-label="All staged records"
        >
          <div className="screening-summary">
            <div>
              <span className="eyebrow">All staged records</span>
              <h2>Project-level staging queue</h2>
              <p className="muted-copy">
                {allStaged.records} candidates staged across{" "}
                {allStaged.runs.length} imports. Use this view to compare
                imports side by side and inspect potential duplicates before
                promoting records from individual runs.
              </p>
            </div>
            <div
              className="screening-counts"
              aria-label="All staged status counts"
            >
              {Object.entries(allStaged.status_counts ?? {}).map(
                ([status, count]) => (
                  <span className={`status-pill ${status}`} key={status}>
                    {status}: {String(count)}
                  </span>
                ),
              )}
              <span className="status-pill">
                duplicate groups: {duplicateGroups.length}
              </span>
            </div>
          </div>
          <div className="screening-toolbar">
            <label>
              Filter all staged records
              <input
                placeholder="Title, author, PMID, DOI, journal, run…"
                value={candidateFilter}
                onChange={(event) => setCandidateFilter(event.target.value)}
              />
            </label>
            <div className="section-actions">
              <button type="button" onClick={selectVisibleAllCandidates}>
                Select visible
              </button>
              <button
                type="button"
                className="button-secondary"
                onClick={clearVisibleAllCandidates}
              >
                Clear visible
              </button>
            </div>
          </div>
          <p className="muted-copy">
            Selected {selectedAllCandidateIds.length} records (
            {selectedAllVisibleCount} visible). Decisions here can span imports;
            dataset creation remains scoped to one staged import at a time.
          </p>

          <section className="screening-panel" aria-label="Possible duplicates">
            <div className="section-heading compact">
              <span className="eyebrow">Deduplication</span>
              <h2>Possible duplicate groups</h2>
              <p>
                Groups are detected from stable identifiers first, then exact
                title/year/first-author keys when identifiers are unavailable.
              </p>
            </div>
            <DataTable
              rows={duplicateGroups}
              emptyMessage="No duplicate groups were detected across staged records."
              columns={[
                { key: "label", header: "Record" },
                { key: "size", header: "Records" },
                { key: "match_basis", header: "Match" },
                {
                  key: "screening_run_names",
                  header: "Imports",
                  render: (row) => row.screening_run_names.join("; "),
                },
                {
                  key: "confidence",
                  header: "Confidence",
                  render: (row) => (
                    <span className="status-pill">{row.confidence}</span>
                  ),
                },
              ]}
            />
          </section>

          <DataTable
            rows={visibleAllCandidates}
            caption={`Showing ${visibleAllCandidates.length} of ${allStaged.records} staged records`}
            emptyMessage="No staged records match the current filter."
            columns={[
              {
                key: "id",
                header: "Mark",
                render: (row) => (
                  <input
                    type="checkbox"
                    aria-label={`Select ${row.title} from ${row.screening_run_name}`}
                    checked={selectedAllCandidateIds.includes(row.id)}
                    disabled={!isImportable(row.status)}
                    onChange={() => toggleAllCandidate(row.id)}
                  />
                ),
              },
              {
                key: "screening_run_name",
                header: "Import",
                render: (row) => (
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => activateRun(row.screening_run_id)}
                  >
                    {row.screening_run_name}
                  </button>
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
              {
                key: "duplicate_group_id",
                header: "Duplicate group",
                render: (row) =>
                  row.duplicate_group_id ? (
                    <span className="status-pill duplicate">
                      {duplicateLabel(row)}
                    </span>
                  ) : (
                    "—"
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
                header: "Journal/source",
                render: (row) => row.source_title ?? "—",
              },
              {
                key: "source_label",
                header: "Provider",
                render: (row) => row.source_label ?? "—",
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
              onClick={() => applyAllCandidateDecision("selected")}
              disabled={
                !selectedAllCandidateIds.length ||
                updateAllScreeningCandidates.isPending
              }
            >
              Mark selected as keep
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={() => applyAllCandidateDecision("excluded")}
              disabled={
                !selectedAllCandidateIds.length ||
                updateAllScreeningCandidates.isPending
              }
            >
              Exclude selected
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={() => applyAllCandidateDecision("maybe")}
              disabled={
                !selectedAllCandidateIds.length ||
                updateAllScreeningCandidates.isPending
              }
            >
              Mark as maybe
            </button>
            <button
              type="button"
              className="button-secondary"
              onClick={() => applyAllCandidateDecision("duplicate")}
              disabled={
                !selectedAllCandidateIds.length ||
                updateAllScreeningCandidates.isPending
              }
            >
              Mark duplicate
            </button>
          </div>
          {updateAllScreeningCandidates.isError && (
            <p role="alert">{updateAllScreeningCandidates.error.message}</p>
          )}
        </div>
      )}
      {screeningView === "run" && stagedRun && (
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
