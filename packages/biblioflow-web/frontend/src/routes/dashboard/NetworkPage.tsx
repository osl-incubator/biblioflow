import { FormEvent, useMemo, useState } from "react";

import { DataTable } from "../../components/common/DataTable";
import { EmptyState } from "../../components/common/EmptyState";
import { useNetwork } from "../../api/queries";
import type { MatrixRequest } from "../../api/types";
import { useActiveWorkspace } from "./workspace";

const networkKinds = [
  "co_occurrence",
  "collaboration",
  "co_citation",
  "bibliographic_coupling",
  "direct_citation",
];

const networkUnits = [
  "keywords_all",
  "authors",
  "references",
  "countries",
  "affiliations",
];

export function NetworkPage() {
  const { projectId, activeDatasetId } = useActiveWorkspace();
  const network = useNetwork(projectId, activeDatasetId);
  const [kind, setKind] = useState("co_occurrence");
  const [unit, setUnit] = useState("keywords_all");
  const [normalize, setNormalize] = useState("");
  const [minOccurrences, setMinOccurrences] = useState(1);

  const request = useMemo<MatrixRequest>(
    () => ({
      kind,
      unit,
      normalize: normalize || null,
      min_occurrences: minOccurrences,
      filters: {},
    }),
    [kind, minOccurrences, normalize, unit],
  );

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    network.mutate(request);
  }

  return (
    <div className="page-stack">
      <section className="card section-heading">
        <span className="eyebrow">Networks</span>
        <h2>Build node and edge structures</h2>
        <p>
          The current UI displays network tables without a heavy visualization
          dependency. A graph canvas can be added after the biblioflow network
          APIs stabilize.
        </p>
      </section>

      <section className="dashboard-grid">
        <form className="card form-card" onSubmit={onSubmit}>
          <div className="section-heading compact">
            <span className="eyebrow">Request</span>
            <h2>Network settings</h2>
          </div>
          <label>
            Network kind
            <select
              value={kind}
              onChange={(event) => setKind(event.target.value)}
            >
              {networkKinds.map((option) => (
                <option key={option} value={option}>
                  {option.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Unit
            <select
              value={unit}
              onChange={(event) => setUnit(event.target.value)}
            >
              {networkUnits.map((option) => (
                <option key={option} value={option}>
                  {option.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <label>
            Normalization
            <select
              value={normalize}
              onChange={(event) => setNormalize(event.target.value)}
            >
              <option value="">None</option>
              <option value="association">Association strength</option>
            </select>
          </label>
          <label>
            Minimum occurrences
            <input
              type="number"
              min="1"
              value={minOccurrences}
              onChange={(event) =>
                setMinOccurrences(Math.max(Number(event.target.value), 1))
              }
            />
          </label>
          <button
            type="submit"
            className="button-primary"
            disabled={network.isPending}
          >
            {network.isPending ? "Building…" : "Build network"}
          </button>
          {network.isError && <p role="alert">{network.error.message}</p>}
        </form>

        <article className="card network-preview-card">
          <span className="eyebrow">Preview</span>
          <h2>Network summary</h2>
          {network.data ? (
            <div className="metric-list">
              <div>
                <span>Nodes</span>
                <strong>{network.data.data.nodes.length}</strong>
              </div>
              <div>
                <span>Edges</span>
                <strong>{network.data.data.edges.length}</strong>
              </div>
              <div>
                <span>Kind</span>
                <strong>
                  {String(network.data.data.metadata?.kind ?? kind)}
                </strong>
              </div>
            </div>
          ) : (
            <div className="placeholder-visual compact-visual">
              <span />
              <span />
              <span />
              <span />
            </div>
          )}
        </article>
      </section>

      <section className="dashboard-grid">
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Nodes</span>
            <h2>Network nodes</h2>
          </div>
          {network.data ? (
            <DataTable
              rows={network.data.data.nodes.slice(0, 50)}
              columns={[
                { key: "label", header: "Label" },
                { key: "occurrences", header: "Occurrences" },
                { key: "degree", header: "Degree" },
                { key: "strength", header: "Strength" },
              ]}
            />
          ) : (
            <EmptyState title="No nodes yet" icon="○">
              <p>Build a network to populate this table.</p>
            </EmptyState>
          )}
        </article>
        <article className="card">
          <div className="section-heading compact">
            <span className="eyebrow">Edges</span>
            <h2>Network edges</h2>
          </div>
          {network.data ? (
            <DataTable
              rows={network.data.data.edges.slice(0, 50)}
              columns={[
                { key: "source", header: "Source" },
                { key: "target", header: "Target" },
                { key: "weight", header: "Weight" },
              ]}
            />
          ) : (
            <EmptyState title="No edges yet" icon="—">
              <p>Build a network to populate this table.</p>
            </EmptyState>
          )}
        </article>
      </section>
    </div>
  );
}
