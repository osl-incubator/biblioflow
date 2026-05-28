import { ChangeEvent, DragEvent, FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { DataTable } from "../components/common/DataTable";
import { EmptyState } from "../components/common/EmptyState";
import {
  useDeleteUpload,
  useLoadDataset,
  useProject,
  usePromoteRemoteCandidates,
  useRemoteSearch,
  useRemoteSearches,
  useSearchRemoteSource,
  useUpdateRemoteCandidates,
  useUploadFiles,
  useUploads,
} from "../api/queries";
import type { RemoteCandidate, RemoteSource } from "../api/types";
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
const remoteSourceOptions: { label: string; value: RemoteSource }[] = [
  { label: "PubMed", value: "pubmed" },
  { label: "PubMed Central", value: "pmc" },
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

function candidateMatches(candidate: RemoteCandidate, query: string): boolean {
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

function identifiersText(candidate: RemoteCandidate): string {
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
  const [remoteSource, setRemoteSource] = useState<RemoteSource>("pubmed");
  const [remoteQuery, setRemoteQuery] = useState("");
  const [remoteLimit, setRemoteLimit] = useState(100);
  const [remoteEmail, setRemoteEmail] = useState("");
  const [remoteApiKey, setRemoteApiKey] = useState("");
  const [remoteTool, setRemoteTool] = useState("biblioflow-web");
  const [remoteName, setRemoteName] = useState("");
  const [activeRemoteSearchId, setActiveRemoteSearchId] = useState<
    string | null
  >(null);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>(
    [],
  );
  const [candidateFilter, setCandidateFilter] = useState("");
  const [hasAutoSelectedUploads, setHasAutoSelectedUploads] = useState(false);
  const remoteSearches = useRemoteSearches(projectId);
  const remoteSearch = useRemoteSearch(projectId, activeRemoteSearchId);
  const searchRemoteSource = useSearchRemoteSource(projectId);
  const updateRemoteCandidates = useUpdateRemoteCandidates(
    projectId,
    activeRemoteSearchId,
  );
  const promoteRemoteCandidates = usePromoteRemoteCandidates(
    projectId,
    activeRemoteSearchId,
  );
  const stagedSearch =
    remoteSearch.data?.data ??
    (searchRemoteSource.data?.data.search_id === activeRemoteSearchId
      ? searchRemoteSource.data.data
      : null);
  const visibleCandidates =
    stagedSearch?.candidates.filter((candidate) =>
      candidateMatches(candidate, candidateFilter),
    ) ?? [];
  const promotableVisibleCandidateIds = visibleCandidates
    .filter(
      (candidate) =>
        candidate.status !== "excluded" && candidate.status !== "imported",
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
    searchRemoteSource.mutate(
      {
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
          setActiveRemoteSearchId(response.data.search_id);
          setSelectedCandidateIds(
            response.data.candidates.map((candidate) => candidate.candidate_id),
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
    status: "candidate" | "selected" | "excluded",
  ) {
    updateRemoteCandidates.mutate(
      { candidate_ids: selectedCandidateIds, status },
      {
        onSuccess: () => {
          if (status === "excluded") {
            setSelectedCandidateIds([]);
          }
        },
      },
    );
  }

  function promoteSelectedCandidates() {
    promoteRemoteCandidates.mutate(
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
          <h2>Search PubMed or PMC</h2>
        </div>
        <p className="muted-copy">
          Search NCBI sources and stage the results as screening candidates
          before creating the active project dataset. Provide a contact email
          here, or configure
          <code>BIBLIOFLOW_NCBI_EMAIL</code> on the backend.
        </p>
        <div className="form-grid">
          <label>
            Source
            <select
              value={remoteSource}
              onChange={(event) =>
                setRemoteSource(event.target.value as RemoteSource)
              }
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
            disabled={!remoteQuery.trim() || searchRemoteSource.isPending}
          >
            {searchRemoteSource.isPending
              ? "Searching…"
              : "Search and review records"}
          </button>
        </div>
        {searchRemoteSource.isError && (
          <p role="alert">{searchRemoteSource.error.message}</p>
        )}
        {remoteSearches.data?.data.length ? (
          <div className="remote-search-history">
            <strong>Recent staged searches</strong>
            <div className="remote-search-list">
              {remoteSearches.data.data.slice(-4).map((search) => (
                <button
                  key={search.search_id}
                  type="button"
                  className={
                    search.search_id === activeRemoteSearchId
                      ? "chip-button active"
                      : "chip-button"
                  }
                  onClick={() => {
                    setActiveRemoteSearchId(search.search_id);
                    setSelectedCandidateIds([]);
                  }}
                >
                  {search.name} · {search.records}
                </button>
              ))}
            </div>
          </div>
        ) : null}
        {stagedSearch && (
          <div
            className="screening-panel"
            role="region"
            aria-label="Screening candidates"
          >
            <div className="screening-summary">
              <div>
                <span className="eyebrow">Screening queue</span>
                <h3>{stagedSearch.name}</h3>
                <p className="muted-copy">
                  {stagedSearch.candidates.length} candidates staged from{" "}
                  {stagedSearch.source_label}. Select records to promote into
                  the active dataset, or mark obvious misses as excluded.
                </p>
              </div>
              <div
                className="screening-counts"
                aria-label="Candidate status counts"
              >
                {Object.entries(stagedSearch.status_counts ?? {}).map(
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
                        row.status === "excluded" || row.status === "imported"
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
                  updateRemoteCandidates.isPending
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
                  updateRemoteCandidates.isPending
                }
              >
                Exclude selected
              </button>
              <button
                type="button"
                className="button-primary"
                onClick={promoteSelectedCandidates}
                disabled={
                  !selectedCandidateIds.length ||
                  promoteRemoteCandidates.isPending
                }
              >
                {promoteRemoteCandidates.isPending
                  ? "Creating dataset…"
                  : "Create dataset from selected"}
              </button>
            </div>
            {updateRemoteCandidates.isError && (
              <p role="alert">{updateRemoteCandidates.error.message}</p>
            )}
            {promoteRemoteCandidates.isError && (
              <p role="alert">{promoteRemoteCandidates.error.message}</p>
            )}
          </div>
        )}
        {promoteRemoteCandidates.data?.data && (
          <div className="success-callout" role="status">
            Created dataset{" "}
            <code>{promoteRemoteCandidates.data.data.dataset_id}</code> from{" "}
            <strong>{promoteRemoteCandidates.data.data.records.length}</strong>{" "}
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
          <button
            type="submit"
            className="button-primary"
            disabled={!selectedUploadIds.length || loadDataset.isPending}
          >
            {loadDataset.isPending
              ? "Loading dataset…"
              : "Load selected uploads"}
          </button>
          {loadDataset.isError && (
            <p role="alert">{loadDataset.error.message}</p>
          )}
        </form>
      </section>
    </div>
  );
}
