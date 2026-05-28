import { ChangeEvent, DragEvent, FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { DataTable } from "../components/common/DataTable";
import { EmptyState } from "../components/common/EmptyState";
import {
  useCreateScreeningRun,
  useDeleteUpload,
  useLoadDataset,
  useProject,
  usePromoteScreeningCandidates,
  useScreeningRun,
  useScreeningRuns,
  useUpdateScreeningCandidates,
  useUploadFiles,
  useUploads,
} from "../api/queries";
import type { ScreeningCandidate } from "../api/types";
import { formatDate } from "./dashboard/utils";

const supportedSources = [
  "Scopus",
  "Web of Science",
  "PubMed",
  "OpenAlex",
  "Crossref",
  "RIS",
  "BibTeX",
  "CSV/TSV/JSON/XML/NBIB/YAML",
];

const providerOptions = [
  "auto",
  "scopus",
  "wos",
  "pubmed",
  "pmc",
  "openalex",
  "crossref",
  "generic",
];
const formatOptions = [
  "auto",
  "ris",
  "bibtex",
  "csv",
  "tsv",
  "json",
  "jsonl",
  "xml",
  "nbib",
  "yaml",
];
const remoteSourceOptions: { label: string; value: string }[] = [
  { label: "PubMed", value: "pubmed" },
  { label: "PubMed Central", value: "pmc" },
  { label: "OpenAlex", value: "openalex" },
  { label: "Crossref", value: "crossref" },
  { label: "Scopus", value: "scopus" },
];

function formatSize(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

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

export function UploadPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const project = useProject(projectId);
  const uploads = useUploads(projectId);
  const uploadFiles = useUploadFiles(projectId);
  const loadDataset = useLoadDataset(projectId);
  const deleteUpload = useDeleteUpload(projectId);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedUploadIds, setSelectedUploadIds] = useState<string[]>([]);
  const [provider, setProvider] = useState("auto");
  const [format, setFormat] = useState("auto");
  const [remoteSource, setRemoteSource] = useState("pubmed");
  const [remoteQuery, setRemoteQuery] = useState("");
  const [remoteLimit, setRemoteLimit] = useState(100);
  const [remoteEmail, setRemoteEmail] = useState("");
  const [remoteApiKey, setRemoteApiKey] = useState("");
  const [remoteTool, setRemoteTool] = useState("biblioflow-web");
  const [remoteName, setRemoteName] = useState("");
  const [activeScreeningRunId, setActiveScreeningRunId] = useState<
    string | null
  >(null);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>(
    [],
  );
  const [candidateFilter, setCandidateFilter] = useState("");
  const [screeningAction, setScreeningAction] = useState<
    "remote" | "uploads" | null
  >(null);
  const [hasAutoSelectedUploads, setHasAutoSelectedUploads] = useState(false);
  const screeningRuns = useScreeningRuns(projectId);
  const screeningRun = useScreeningRun(projectId, activeScreeningRunId);
  const createScreeningRun = useCreateScreeningRun(projectId);
  const updateScreeningCandidates = useUpdateScreeningCandidates(
    projectId,
    activeScreeningRunId,
  );
  const promoteScreeningCandidates = usePromoteScreeningCandidates(
    projectId,
    activeScreeningRunId,
  );
  const stagedRun =
    screeningRun.data?.data ??
    (createScreeningRun.data?.data.screening_run_id === activeScreeningRunId
      ? createScreeningRun.data.data
      : null);
  const visibleCandidates =
    stagedRun?.candidates.filter((candidate) =>
      candidateMatches(candidate, candidateFilter),
    ) ?? [];
  const promotableVisibleCandidateIds = visibleCandidates
    .filter(
      (candidate) =>
        !["excluded", "duplicate", "imported", "error"].includes(
          candidate.status,
        ),
    )
    .map((candidate) => candidate.candidate_id);
  const selectedVisibleCount = visibleCandidates.filter((candidate) =>
    selectedCandidateIds.includes(candidate.candidate_id),
  ).length;

  useEffect(() => {
    if (!hasAutoSelectedUploads && uploads.data?.data.length) {
      setSelectedUploadIds(uploads.data.data.map((upload) => upload.upload_id));
      setHasAutoSelectedUploads(true);
    }
  }, [hasAutoSelectedUploads, uploads.data?.data]);

  function addFiles(files: FileList | File[]) {
    setSelectedFiles((current) => [...current, ...Array.from(files)]);
  }

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    if (event.target.files) {
      addFiles(event.target.files);
    }
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    if (event.dataTransfer.files.length) {
      addFiles(event.dataTransfer.files);
    }
  }

  function onUpload() {
    uploadFiles.mutate(selectedFiles, {
      onSuccess: (response) => {
        setSelectedFiles([]);
        setSelectedUploadIds((current) => [
          ...new Set([
            ...current,
            ...response.data.map((upload) => upload.upload_id),
          ]),
        ]);
      },
    });
  }

  function toggleUpload(uploadId: string) {
    setSelectedUploadIds((current) =>
      current.includes(uploadId)
        ? current.filter((item) => item !== uploadId)
        : [...current, uploadId],
    );
  }

  function onLoadDataset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loadDataset.mutate(
      {
        upload_ids: selectedUploadIds,
        provider,
        format,
      },
      {
        onSuccess: (response) => {
          const target = response.warnings.length ? "validation" : "overview";
          navigate(`/projects/${projectId}/dashboard/${target}`);
        },
      },
    );
  }

  function onImportRemoteSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setScreeningAction("remote");
    createScreeningRun.mutate(
      {
        origin_type: "remote_search",
        source: remoteSource,
        query: remoteQuery,
        limit: remoteLimit,
        email: remoteEmail.trim() || null,
        api_key: remoteApiKey.trim() || null,
        tool: remoteTool.trim() || "biblioflow-web",
        name: remoteName.trim() || null,
      },
      {
        onSuccess: (response) => {
          setRemoteApiKey("");
          setActiveScreeningRunId(response.data.screening_run_id);
          setSelectedCandidateIds(
            response.data.candidates.map((candidate) => candidate.candidate_id),
          );
        },
      },
    );
  }

  function reviewSelectedUploads() {
    setScreeningAction("uploads");
    createScreeningRun.mutate(
      {
        origin_type: "uploads",
        upload_ids: selectedUploadIds,
        source: provider,
        format,
        name: selectedUploadIds.length
          ? `Uploaded files: ${selectedUploadIds.length} selected`
          : null,
      },
      {
        onSuccess: (response) => {
          setActiveScreeningRunId(response.data.screening_run_id);
          setSelectedCandidateIds(
            response.data.candidates
              .filter((candidate) => candidate.status !== "duplicate")
              .map((candidate) => candidate.candidate_id),
          );
        },
      },
    );
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
        name: remoteName.trim() || null,
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
        <p>Select or create a project before uploading files.</p>
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
          <span className="eyebrow">Search</span>
          <h1>Import or load data</h1>
          <p>
            Upload bibliographic exports, then load one or more uploaded files
            into the project active dataset. The resulting dataset powers every
            analysis panel.
          </p>
        </div>
        <Link
          className="button button-secondary"
          to={`/projects/${projectId}/dashboard/overview`}
        >
          Go to dashboard
        </Link>
      </section>

      <section className="upload-layout">
        <article className="card upload-dropzone">
          <label
            className="dropzone-label"
            onDragOver={(event) => event.preventDefault()}
            onDrop={onDrop}
          >
            <span className="dropzone-icon">⇪</span>
            <h2>Upload bibliographic files</h2>
            <p>Drop files here or choose multiple files from your computer.</p>
            <input type="file" multiple onChange={onFileChange} />
            <span className="button button-primary">Choose files</span>
          </label>
          {selectedFiles.length > 0 && (
            <div className="selected-file-list">
              <strong>Ready to upload</strong>
              <ul>
                {selectedFiles.map((file) => (
                  <li key={`${file.name}-${file.size}`}>
                    {file.name} · {formatSize(file.size)}
                  </li>
                ))}
              </ul>
              <div className="section-actions">
                <button
                  type="button"
                  onClick={onUpload}
                  disabled={uploadFiles.isPending}
                >
                  {uploadFiles.isPending
                    ? "Uploading…"
                    : "Upload selected files"}
                </button>
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() => setSelectedFiles([])}
                >
                  Clear
                </button>
              </div>
            </div>
          )}
          {uploadFiles.isError && (
            <p role="alert">{uploadFiles.error.message}</p>
          )}
        </article>

        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Supported files</span>
            <h2>Database exports</h2>
          </div>
          <div className="capability-grid compact-grid">
            {supportedSources.map((source) => (
              <span className="capability-pill" key={source}>
                {source}
              </span>
            ))}
          </div>
        </article>
      </section>

      <form
        className="card form-card remote-source-card"
        onSubmit={onImportRemoteSource}
      >
        <div className="section-heading compact">
          <span className="eyebrow">Remote sources</span>
          <h2>Search remote sources</h2>
        </div>
        <p className="muted-copy">
          Search a supported API source and stage the results as screening
          candidates before creating the active project dataset. For NCBI
          sources, provide a contact email here or configure
          <code>BIBLIOFLOW_NCBI_EMAIL</code> on the backend.
        </p>
        <div className="form-grid">
          <label>
            Source
            <select
              value={remoteSource}
              onChange={(event) => setRemoteSource(event.target.value)}
            >
              {remoteSourceOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Limit
            <input
              min="1"
              max="1000"
              type="number"
              value={remoteLimit}
              onChange={(event) => setRemoteLimit(Number(event.target.value))}
            />
          </label>
          <label>
            Contact email
            <input
              type="email"
              placeholder="researcher@example.org"
              value={remoteEmail}
              onChange={(event) => setRemoteEmail(event.target.value)}
            />
          </label>
          <label>
            NCBI API key
            <input
              autoComplete="off"
              placeholder="Optional"
              type="password"
              value={remoteApiKey}
              onChange={(event) => setRemoteApiKey(event.target.value)}
            />
          </label>
          <label>
            Tool name
            <input
              value={remoteTool}
              onChange={(event) => setRemoteTool(event.target.value)}
            />
          </label>
          <label>
            Dataset name
            <input
              placeholder="Optional"
              value={remoteName}
              onChange={(event) => setRemoteName(event.target.value)}
            />
          </label>
        </div>
        <label>
          Query
          <textarea
            placeholder="bibliometrics AND reproducibility"
            rows={4}
            value={remoteQuery}
            onChange={(event) => setRemoteQuery(event.target.value)}
          />
        </label>
        <div className="section-actions">
          <button
            type="submit"
            className="button-primary"
            disabled={!remoteQuery.trim() || createScreeningRun.isPending}
          >
            {createScreeningRun.isPending
              ? "Searching…"
              : "Search and review records"}
          </button>
        </div>
        {createScreeningRun.isError && screeningAction === "remote" && (
          <p role="alert">{createScreeningRun.error.message}</p>
        )}
        {screeningRuns.data?.data.length ? (
          <div className="remote-search-history">
            <strong>Recent screening runs</strong>
            <div className="remote-search-list">
              {screeningRuns.data.data.slice(-4).map((run) => (
                <button
                  key={run.screening_run_id}
                  type="button"
                  className={
                    run.screening_run_id === activeScreeningRunId
                      ? "chip-button active"
                      : "chip-button"
                  }
                  onClick={() => {
                    setActiveScreeningRunId(run.screening_run_id);
                    setSelectedCandidateIds([]);
                  }}
                >
                  {run.name} · {run.records}
                </button>
              ))}
            </div>
          </div>
        ) : null}
        {stagedRun && (
          <div
            className="screening-panel"
            role="region"
            aria-label="Screening candidates"
          >
            <div className="screening-summary">
              <div>
                <span className="eyebrow">Screening queue</span>
                <h3>{stagedRun.name}</h3>
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
                      disabled={
                        row.status === "excluded" ||
                        row.status === "duplicate" ||
                        row.status === "imported" ||
                        row.status === "error"
                      }
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
            <strong>
              {promoteScreeningCandidates.data.data.records.length}
            </strong>{" "}
            screened records.
            <Link
              className="button button-secondary"
              to={`/projects/${projectId}/dashboard/overview`}
            >
              Go to dashboard
            </Link>
          </div>
        )}
      </form>

      <section className="dashboard-grid">
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Uploads</span>
            <h2>Project files</h2>
          </div>
          {uploads.isLoading && <p>Loading uploads…</p>}
          {uploads.isError && <p role="alert">Unable to load uploads.</p>}
          {uploads.data?.data.length ? (
            <DataTable
              rows={uploads.data.data}
              columns={[
                {
                  key: "upload_id",
                  header: "Load",
                  render: (row) => (
                    <input
                      type="checkbox"
                      aria-label={`Select ${row.filename}`}
                      checked={selectedUploadIds.includes(row.upload_id)}
                      onChange={() => toggleUpload(row.upload_id)}
                    />
                  ),
                },
                { key: "filename", header: "Filename" },
                { key: "content_type", header: "Type" },
                {
                  key: "size",
                  header: "Size",
                  render: (row) => formatSize(row.size),
                },
                {
                  key: "created_at",
                  header: "Uploaded",
                  render: (row) => formatDate(row.created_at),
                },
                {
                  key: "delete",
                  header: "Actions",
                  render: (row) => (
                    <button
                      type="button"
                      className="link-button danger-link"
                      disabled={deleteUpload.isPending}
                      onClick={() =>
                        deleteUpload.mutate(row.upload_id, {
                          onSuccess: () =>
                            setSelectedUploadIds((current) =>
                              current.filter(
                                (uploadId) => uploadId !== row.upload_id,
                              ),
                            ),
                        })
                      }
                    >
                      Delete
                    </button>
                  ),
                },
              ]}
            />
          ) : (
            !uploads.isLoading && (
              <EmptyState title="No uploaded files" icon="⇪">
                <p>
                  Upload RIS, BibTeX, CSV, JSON, XML, NBIB, or provider exports.
                </p>
              </EmptyState>
            )
          )}
          {deleteUpload.isError && (
            <p role="alert">{deleteUpload.error.message}</p>
          )}
        </article>

        <form className="card form-card" onSubmit={onLoadDataset}>
          <div className="section-heading compact">
            <span className="eyebrow">Load</span>
            <h2>Create active dataset</h2>
          </div>
          <p className="muted-copy">
            Selected uploads: {selectedUploadIds.length}. Loading will normalize
            the records and update the project's active dataset.
          </p>
          <label>
            Provider
            <select
              value={provider}
              onChange={(event) => setProvider(event.target.value)}
            >
              {providerOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label>
            Format
            <select
              value={format}
              onChange={(event) => setFormat(event.target.value)}
            >
              {formatOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <div className="section-actions">
            <button
              type="button"
              onClick={reviewSelectedUploads}
              disabled={
                !selectedUploadIds.length || createScreeningRun.isPending
              }
            >
              {createScreeningRun.isPending
                ? "Creating screening run…"
                : "Review selected uploads"}
            </button>
            <button
              type="submit"
              className="button-primary"
              disabled={!selectedUploadIds.length || loadDataset.isPending}
            >
              {loadDataset.isPending ? "Loading dataset…" : "Load directly"}
            </button>
          </div>
          {createScreeningRun.isError && screeningAction === "uploads" && (
            <p role="alert">{createScreeningRun.error.message}</p>
          )}
          {loadDataset.isError && (
            <p role="alert">{loadDataset.error.message}</p>
          )}
        </form>
      </section>
    </div>
  );
}
