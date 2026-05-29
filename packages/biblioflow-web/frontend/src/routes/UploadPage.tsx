import { ChangeEvent, DragEvent, FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { DataTable } from "../components/common/DataTable";
import { EmptyState } from "../components/common/EmptyState";
import {
  useCreateScreeningRun,
  useDeleteUpload,
  useLoadDataset,
  useProject,
  useUploadFiles,
  useUploads,
} from "../api/queries";
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
  const [screeningAction, setScreeningAction] = useState<
    "remote" | "uploads" | null
  >(null);
  const [hasAutoSelectedUploads, setHasAutoSelectedUploads] = useState(false);
  const createScreeningRun = useCreateScreeningRun(projectId);

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
          navigate(
            `/projects/${projectId}/screening?run=${response.data.screening_run_id}`,
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
          navigate(
            `/projects/${projectId}/screening?run=${response.data.screening_run_id}`,
          );
        },
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
            Screening run name
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
