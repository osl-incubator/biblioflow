import { StatusPanel } from "../components/feedback/StatusPanel";
import { useHealth } from "../api/queries";

export function HomePage() {
  const health = useHealth();

  return (
    <div className="page-stack">
      <section className="hero">
        <h1>Bibliometric analysis in the browser</h1>
        <p>
          Upload bibliographic data, validate records, run biblioflow analyses,
          and explore Biblioshiny-inspired dashboards.
        </p>
      </section>

      <StatusPanel title="Backend status">
        {health.isLoading && <p>Checking API status…</p>}
        {health.isError && <p role="alert">The API is not reachable.</p>}
        {health.data && (
          <dl>
            <dt>Service</dt>
            <dd>{health.data.service}</dd>
            <dt>Status</dt>
            <dd>{health.data.status}</dd>
            <dt>biblioflow</dt>
            <dd>{health.data.biblioflow_version ?? "unknown"}</dd>
          </dl>
        )}
      </StatusPanel>
    </div>
  );
}
