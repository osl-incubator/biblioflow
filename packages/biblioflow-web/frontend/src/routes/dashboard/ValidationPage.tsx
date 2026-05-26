import { DataTable } from "../../components/common/DataTable";
import { EmptyState } from "../../components/common/EmptyState";
import { useDatasetRecords, useValidation } from "../../api/queries";
import type { ApiWarning } from "../../api/types";
import { dynamicColumns, valueToString } from "./utils";
import { useActiveWorkspace } from "./workspace";

interface WarningRow extends Record<string, unknown> {
  id: number;
  level: string;
  type: string;
  field: string;
  record: string;
  message: string;
}

function warningRows(warnings: ApiWarning[] | undefined): WarningRow[] {
  return (warnings ?? []).map((warning, index) => ({
    id: index + 1,
    level: String(warning.level ?? "warning"),
    type: String(warning.type ?? "load"),
    field: String(warning.field ?? "—"),
    record: String(warning.record_index ?? "—"),
    message: String(warning.message ?? valueToString(warning)),
  }));
}

export function ValidationPage() {
  const { projectId, activeDatasetId } = useActiveWorkspace();
  const validation = useValidation(projectId, activeDatasetId);
  const records = useDatasetRecords(projectId, activeDatasetId);
  const rows = warningRows(validation.data?.data.warnings);
  const sampleRecords = (records.data?.data ?? []).slice(0, 5);

  if (validation.isLoading) {
    return <p>Loading validation report…</p>;
  }

  if (validation.isError) {
    return (
      <EmptyState title="Validation report failed" icon="!">
        <p>{validation.error.message}</p>
      </EmptyState>
    );
  }

  return (
    <div className="page-stack">
      <section className="dashboard-grid">
        <article className="card">
          <span className="eyebrow">Validation</span>
          <h2>Dataset quality report</h2>
          <p className="muted-copy">
            Inspect warnings generated during loading and normalization before
            using the dataset for analysis.
          </p>
          <div className="metric-list">
            <div>
              <span>Records</span>
              <strong>{validation.data?.data.records ?? "—"}</strong>
            </div>
            <div>
              <span>Warnings</span>
              <strong>{rows.length}</strong>
            </div>
            <div>
              <span>Dataset</span>
              <strong>{activeDatasetId?.slice(0, 8) ?? "—"}</strong>
            </div>
          </div>
        </article>
        <article className="card">
          <span className="eyebrow">Metadata</span>
          <h2>Load metadata</h2>
          <DataTable
            rows={Object.entries(validation.data?.data.metadata ?? {}).map(
              ([key, value]) => ({ key, value }),
            )}
            columns={[
              { key: "key", header: "Key" },
              {
                key: "value",
                header: "Value",
                render: (row) => valueToString(row.value),
              },
            ]}
            emptyMessage="No metadata was stored for this dataset."
          />
        </article>
      </section>

      <section className="card">
        <div className="section-heading compact">
          <span className="eyebrow">Warnings</span>
          <h2>Load and normalization warnings</h2>
        </div>
        {rows.length ? (
          <DataTable
            rows={rows}
            columns={[
              { key: "level", header: "Level" },
              { key: "type", header: "Type" },
              { key: "field", header: "Field" },
              { key: "record", header: "Record" },
              { key: "message", header: "Message" },
            ]}
          />
        ) : (
          <EmptyState title="No validation warnings" icon="✓">
            <p>The active dataset loaded without stored warnings.</p>
          </EmptyState>
        )}
      </section>

      <section className="card">
        <div className="section-heading compact">
          <span className="eyebrow">Preview</span>
          <h2>Sample normalized records</h2>
        </div>
        <DataTable
          rows={sampleRecords}
          columns={dynamicColumns(sampleRecords)}
          emptyMessage="No records are available for preview."
        />
      </section>
    </div>
  );
}
