import { useEffect, useState } from "react";
import { fetchMetrics } from "./api/client.js";
import { METRICS_POLL_MS } from "./config.js";

function StatTile({ label, value, sub }) {
  return (
    <div className="pp-stat-tile">
      <span className="pp-stat-tile__label">{label}</span>
      <span className="pp-stat-tile__value pp-mono">{value}</span>
      {sub && <span className="pp-stat-tile__sub">{sub}</span>}
    </div>
  );
}

function OutcomeBar({ label, pct, color }) {
  return (
    <div className="pp-outcome-bar">
      <div className="pp-outcome-bar__row">
        <span>{label}</span>
        <span className="pp-mono" style={{ color }}>{pct}%</span>
      </div>
      <div className="pp-outcome-bar__track">
        <div className="pp-outcome-bar__fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

const OUTCOME_COLORS = {
  ok: "#6FD3BE",
  guardrail_input: "#E6C36B",
  guardrail_output: "#E6C36B",
  timeout: "#E88B7D",
  error: "#E88B7D",
};

const OUTCOME_LABELS = {
  ok: "Completed ok",
  guardrail_input: "Input guardrail",
  guardrail_output: "Output guardrail",
  timeout: "Timeout",
  error: "Error",
};

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const data = await fetchMetrics();
        if (!cancelled) {
          setMetrics(data);
          setError(false);
        }
      } catch {
        if (!cancelled) setError(true);
      }
    }

    poll();
    const id = setInterval(poll, METRICS_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const total = metrics?.total ?? 0;
  const outcomes = metrics?.outcomes ?? {};
  const outcomeEntries = Object.entries(outcomes).sort((a, b) => b[1] - a[1]);

  return (
    <div className="pp-dashboard">
      <div className="pp-dashboard__head">
        <svg width="22" height="22" viewBox="0 0 24 24" aria-label="PipelinePilot" role="img">
          <path fill="#f97316" d="M3 11.5 21 3l-8.5 18-2.2-7.3z" />
        </svg>
        <span className="pp-dashboard__title">PipelinePilot - operations</span>
        <span className="pp-pill pp-pill--teal-dark">reads /metrics</span>
        <div className="pp-header__spacer" />
        {error && <span className="pp-error-text">Could not reach /metrics</span>}
      </div>

      <div className="pp-stat-grid">
        <StatTile label="Total turns" value={total} sub="since server start" />
        <StatTile
          label="Error rate"
          value={metrics ? `${(metrics.error_rate * 100).toFixed(1)}%` : "-"}
        />
        <StatTile
          label="Latency p50 / p95"
          value={metrics ? `${(metrics.latency_p50_ms / 1000).toFixed(1)}s / ${(metrics.latency_p95_ms / 1000).toFixed(1)}s` : "-"}
          sub="full turn, end to end"
        />
        <StatTile
          label="Active sessions"
          value={metrics ? `${metrics.active_sessions} / ${metrics.max_sessions}` : "-"}
        />
      </div>

      <div className="pp-dashboard__panels">
        <div className="pp-panel pp-panel--dark">
          <span className="pp-panel__title">Time to first event vs full turn</span>
          {metrics ? (
            <div className="pp-latency-bars">
              <LatencyPair label="p50" first={metrics.ttft_p50_ms} full={metrics.latency_p50_ms} />
              <LatencyPair label="p95" first={metrics.ttft_p95_ms} full={metrics.latency_p95_ms} />
              <div className="pp-latency-legend">
                <span><span className="pp-dot" style={{ background: "#6FD3BE" }} /> first event</span>
                <span><span className="pp-dot" style={{ background: "#0B7A66" }} /> full turn</span>
              </div>
            </div>
          ) : (
            <span className="pp-muted">Loading...</span>
          )}
        </div>

        <div className="pp-panel pp-panel--dark">
          <span className="pp-panel__title">Outcomes</span>
          <div className="pp-outcome-list">
            {outcomeEntries.length === 0 && <span className="pp-muted">No turns yet.</span>}
            {outcomeEntries.map(([key, count]) => (
              <OutcomeBar
                key={key}
                label={OUTCOME_LABELS[key] ?? key}
                pct={total > 0 ? Math.round((count / total) * 100) : 0}
                color={OUTCOME_COLORS[key] ?? "#8A97A8"}
              />
            ))}
          </div>
          {metrics && (
            <div className="pp-panel__footnote">
              avg tool calls per turn <span className="pp-mono">{metrics.avg_tool_calls}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function LatencyPair({ label, first, full }) {
  const maxMs = 15000; // scales the bars; adjust if your turns run much longer
  const firstPct = Math.min(100, ((first ?? 0) / maxMs) * 100);
  const fullPct = Math.min(100, ((full ?? 0) / maxMs) * 100);

  return (
    <div className="pp-latency-pair">
      <div className="pp-latency-pair__bars">
        <div className="pp-latency-pair__bar" style={{ height: `${firstPct}%`, background: "#6FD3BE" }} />
        <div className="pp-latency-pair__bar" style={{ height: `${fullPct}%`, background: "#0B7A66" }} />
      </div>
      <span className="pp-muted">{label}</span>
    </div>
  );
}
