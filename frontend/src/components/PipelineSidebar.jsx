const STATUS_STYLE = {
  // Falls back to the "applied" look for any status string the backend
  // sends that isn't one of these two, so a new status never breaks layout.
  follow_up: { label: "Follow up", bg: "#FEF3C7", fg: "#92400E" },
  interviewing: { label: "Interviewing", bg: "#E3F4F0", fg: "#075E4E" },
  applied: { label: "Applied", bg: "#EEF1F5", fg: "#334155" },
};

function StatusPill({ status }) {
  const style = STATUS_STYLE[status] ?? STATUS_STYLE.applied;
  return (
    <span
      className="pp-status-pill"
      style={{ background: style.bg, color: style.fg }}
    >
      {style.label}
    </span>
  );
}

export default function PipelineSidebar({ applications, loading, error }) {
  return (
    <aside className="pp-sidebar">
      <div className="pp-sidebar__head">
        <h2>Pipeline</h2>
        <span className="pp-muted">
          {loading ? "Loading..." : `${applications.length} applications`}
        </span>
      </div>

      {error && <p className="pp-error-text">Could not load the pipeline.</p>}

      <div className="pp-sidebar__list">
        {applications.map((app) => (
          <div className="pp-app-card" key={`${app.company}-${app.role}`}>
            <div className="pp-app-card__top">
              <span className="pp-app-card__company">{app.company}</span>
              <StatusPill status={app.status} />
            </div>
            <span className="pp-muted">{app.role}</span>
            {app.last_activity_date && (
              <span className="pp-muted pp-muted--small">
                Last activity {app.last_activity_date}
              </span>
            )}
          </div>
        ))}
      </div>

      <p className="pp-sidebar__note">
        Read-only view of the demo database. Your changes only affect your own
        session.
      </p>
    </aside>
  );
}
