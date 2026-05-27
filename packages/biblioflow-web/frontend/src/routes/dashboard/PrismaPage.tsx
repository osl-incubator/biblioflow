import { FormEvent, useEffect, useMemo, useState } from "react";

import { DataTable } from "../../components/common/DataTable";
import { EmptyState } from "../../components/common/EmptyState";
import { useBuildPrismaFlow, usePrismaFlow } from "../../api/queries";
import type { PrismaFlowPayload } from "../../api/types";
import { valueToString } from "./utils";
import { useActiveWorkspace } from "./workspace";

const countFields = [
  ["records_identified_databases", "Records identified from databases"],
  ["records_identified_registers", "Records identified from registers"],
  ["records_removed_duplicates", "Duplicate records removed"],
  ["records_removed_automation", "Records removed by automation"],
  ["records_removed_other", "Records removed for other reasons"],
  ["records_screened", "Records screened"],
  ["records_excluded", "Records excluded at screening"],
  ["reports_sought", "Reports sought for retrieval"],
  ["reports_not_retrieved", "Reports not retrieved"],
  ["reports_assessed", "Reports assessed for eligibility"],
  ["reports_excluded_total", "Reports excluded after assessment"],
  ["studies_included", "Studies included"],
  ["reports_included", "Reports included"],
] as const;

const countLabels = new Map<string, string>([
  ...countFields,
  ["reports_excluded", "Reports excluded by reason"],
]);

function countValue(
  payload: PrismaFlowPayload | undefined,
  key: string,
): string {
  const value = payload?.counts[key];
  if (typeof value === "number") {
    return String(value);
  }
  if (typeof value === "string") {
    return value;
  }
  return "0";
}

function numericCounts(values: Record<string, string>): Record<string, number> {
  return Object.fromEntries(
    countFields.map(([key]) => [key, Math.max(Number(values[key] || 0), 0)]),
  );
}

function validationRows(payload: PrismaFlowPayload | undefined) {
  const errors = payload?.validation.errors ?? [];
  const warnings = payload?.validation.warnings ?? [];
  return [...errors, ...warnings].map((message, index) => ({
    id: index + 1,
    level: message.level,
    field: message.field,
    message: message.message,
    expected: message.expected ?? "—",
    found: message.found ?? "—",
  }));
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

function safeFilename(value: unknown): string {
  const slug = String(value ?? "prisma-diagram")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug || "prisma-diagram";
}

function svgSize(svg: string): { width: number; height: number } {
  const width = Number.parseFloat(svg.match(/\bwidth="([^"]+)"/)?.[1] ?? "");
  const height = Number.parseFloat(svg.match(/\bheight="([^"]+)"/)?.[1] ?? "");
  if (Number.isFinite(width) && Number.isFinite(height)) {
    return { width, height };
  }

  const viewBox = svg
    .match(/\bviewBox="([^"]+)"/)?.[1]
    ?.trim()
    .split(/\s+/)
    .map(Number);
  if (viewBox?.length === 4 && viewBox.every(Number.isFinite)) {
    return { width: viewBox[2], height: viewBox[3] };
  }

  return { width: 1200, height: 900 };
}

function loadSvgImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () =>
      reject(new Error("Unable to load SVG for PNG export."));
    image.src = url;
  });
}

async function svgToPngBlob(svg: string): Promise<Blob> {
  const { width, height } = svgSize(svg);
  const svgUrl = URL.createObjectURL(
    new Blob([svg], { type: "image/svg+xml;charset=utf-8" }),
  );
  try {
    const image = await loadSvgImage(svgUrl);
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");
    if (!context) {
      throw new Error("Unable to prepare PNG export canvas.");
    }

    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, width, height);
    context.drawImage(image, 0, 0, width, height);

    return await new Promise((resolve, reject) => {
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob);
          return;
        }
        reject(new Error("Unable to create PNG export."));
      }, "image/png");
    });
  } finally {
    URL.revokeObjectURL(svgUrl);
  }
}

export function PrismaPage() {
  const { projectId, activeDatasetId } = useActiveWorkspace();
  const defaultPrisma = usePrismaFlow(projectId, activeDatasetId);
  const buildPrisma = useBuildPrismaFlow(projectId);
  const [title, setTitle] = useState("");
  const [counts, setCounts] = useState<Record<string, string>>({});
  const [isDirty, setIsDirty] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const activePayload = buildPrisma.data?.data ?? defaultPrisma.data?.data;
  const activeSvg = activePayload?.renders.svg ?? "";
  const downloadBaseName = safeFilename(activePayload?.flow.title ?? title);
  const rows = validationRows(activePayload);
  const countRows = useMemo(
    () =>
      Object.entries(activePayload?.counts ?? {}).map(([key, value]) => ({
        key: countLabels.get(key) ?? key.replaceAll("_", " "),
        value,
      })),
    [activePayload?.counts],
  );

  function downloadSvg() {
    if (!activeSvg) {
      return;
    }
    setDownloadError(null);
    downloadBlob(
      new Blob([activeSvg], { type: "image/svg+xml;charset=utf-8" }),
      `${downloadBaseName}.svg`,
    );
  }

  async function downloadPng() {
    if (!activeSvg) {
      return;
    }
    setDownloadError(null);
    try {
      downloadBlob(await svgToPngBlob(activeSvg), `${downloadBaseName}.png`);
    } catch (error) {
      setDownloadError(
        error instanceof Error
          ? error.message
          : "Unable to download the PRISMA diagram as PNG.",
      );
    }
  }

  useEffect(() => {
    if (!defaultPrisma.data?.data || isDirty) {
      return;
    }
    const payload = defaultPrisma.data.data;
    setTitle(String(payload.flow.title ?? ""));
    setCounts(
      Object.fromEntries(
        countFields.map(([key]) => [key, countValue(payload, key)]),
      ),
    );
  }, [defaultPrisma.data?.data, isDirty]);

  function updateCount(key: string, value: string) {
    setIsDirty(true);
    setCounts((current) => ({ ...current, [key]: value }));
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    buildPrisma.mutate({
      dataset_id: activeDatasetId,
      title,
      counts: numericCounts(counts),
    });
  }

  if (defaultPrisma.isLoading) {
    return <p>Generating PRISMA flow…</p>;
  }

  if (defaultPrisma.isError) {
    return (
      <EmptyState title="PRISMA flow generation failed" icon="!">
        <p>{defaultPrisma.error.message}</p>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack">
      <section className="card section-heading">
        <span className="eyebrow">Appraisal</span>
        <h2>PRISMA diagram</h2>
        <p>
          Generate a PRISMA flow diagram with the prismaflow package. The
          default counts are derived from the active biblioflow dataset, and the
          fields below can be adjusted to match the review screening process.
        </p>
      </section>

      <section className="dashboard-grid prisma-grid">
        <form className="card form-card" onSubmit={onSubmit}>
          <div className="section-heading compact">
            <span className="eyebrow">Counts</span>
            <h2>Review flow inputs</h2>
          </div>
          <label>
            Diagram title
            <input
              value={title}
              onChange={(event) => {
                setIsDirty(true);
                setTitle(event.target.value);
              }}
            />
          </label>
          <div className="form-grid two-columns">
            {countFields.map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  type="number"
                  min="0"
                  value={counts[key] ?? "0"}
                  onChange={(event) => updateCount(key, event.target.value)}
                />
              </label>
            ))}
          </div>
          <button
            type="submit"
            className="button-primary"
            disabled={buildPrisma.isPending}
          >
            {buildPrisma.isPending ? "Rendering…" : "Render PRISMA diagram"}
          </button>
          {buildPrisma.isError && (
            <p role="alert">{buildPrisma.error.message}</p>
          )}
        </form>

        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Validation</span>
            <h2>Count relationships</h2>
          </div>
          {rows.length ? (
            <DataTable
              rows={rows}
              columns={[
                { key: "level", header: "Level" },
                { key: "field", header: "Field" },
                { key: "message", header: "Message" },
                { key: "expected", header: "Expected" },
                { key: "found", header: "Found" },
              ]}
            />
          ) : (
            <EmptyState title="PRISMA validation passed" icon="✓">
              <p>No count relationship issues were reported by prismaflow.</p>
            </EmptyState>
          )}
        </article>
      </section>

      <section className="card">
        <div className="section-heading compact">
          <span className="eyebrow">Preview</span>
          <h2>Rendered SVG</h2>
          <div className="section-actions">
            <button
              type="button"
              className="button-secondary"
              disabled={!activeSvg}
              onClick={downloadSvg}
            >
              Download SVG
            </button>
            <button
              type="button"
              className="button-secondary"
              disabled={!activeSvg}
              onClick={() => void downloadPng()}
            >
              Download PNG
            </button>
          </div>
        </div>
        {downloadError && <p role="alert">{downloadError}</p>}
        {activeSvg ? (
          <div
            className="prisma-svg-preview"
            dangerouslySetInnerHTML={{ __html: activeSvg }}
          />
        ) : (
          <EmptyState title="No PRISMA preview yet" icon="▧">
            <p>Render the current counts to preview the diagram.</p>
          </EmptyState>
        )}
      </section>

      <section className="dashboard-grid">
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Resolved counts</span>
            <h2>Current PRISMA model inputs</h2>
          </div>
          <DataTable
            rows={countRows}
            columns={[
              { key: "key", header: "Count" },
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
            <span className="eyebrow">Mermaid</span>
            <h2>Text export</h2>
          </div>
          <textarea
            className="code-textarea"
            readOnly
            value={activePayload?.renders.mermaid ?? ""}
            aria-label="PRISMA Mermaid text"
          />
        </article>
      </section>
    </div>
  );
}
