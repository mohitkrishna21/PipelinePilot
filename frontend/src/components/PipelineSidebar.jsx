const STATUS_STYLE = {
  applied: { label: "Applied", bg: "#EEF1F5", fg: "#334155" },
  phone_screen: { label: "Phone Screen", bg: "#DBEAFE", fg: "#1E40AF" },
  onsite: { label: "Onsite", bg: "#EDE9FE", fg: "#5B21B6" },
  offer: { label: "Offer", bg: "#D1FAE5", fg: "#065F46" },
  rejected: { label: "Rejected", bg: "#FEE2E2", fg: "#991B1B" },
  follow_up: { label: "Follow up", bg: "#FEF3C7", fg: "#92400E" },
};

function titleCase(str) {
  return str
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function StatusPill({ status }) {
  const style = STATUS_STYLE[status] ?? {
    label: titleCase(status ?? "unknown"),
    bg: "#EEF1F5",
    fg: "#334155",
  };
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
              <StatusPill status={app.current_stage} />
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