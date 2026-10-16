// Work-authorization badge: four states, colour follows how much it matters
// to a visa-sponsored candidate. Keys match what the backend's JDBreakdown
// is expected to send in `work_authorization`; if your real field uses
// different enum values, tell me and I'll adjust this one map.
const AUTH_STYLE = {
  citizens_or_us_persons_only: {
    label: "US persons only",
    bg: "#FDECEC",
    fg: "#912018",
    iconStroke: "#B42318",
  },
  no_sponsorship: {
    label: "No sponsorship",
    bg: "#FEF3C7",
    fg: "#7A3410",
    iconStroke: "#92400E",
  },
  sponsorship_offered: {
    label: "Sponsorship offered",
    bg: "#E3F4F0",
    fg: "#075E4E",
    iconStroke: "#075E4E",
  },
  not_stated: {
    label: "Not stated",
    bg: "#EEF1F5",
    fg: "#334155",
    iconStroke: "#5B6676",
  },
};

function AuthBadge({ status, quote }) {
  const style = AUTH_STYLE[status] ?? AUTH_STYLE.not_stated;
  return (
    <div className="pp-auth-badge" style={{ background: style.bg }}>
      <div className="pp-auth-badge__label" style={{ color: style.fg }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={style.iconStroke}
             strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v5M12 16v.5" />
        </svg>
        <span>Work authorization: {style.label}</span>
      </div>
      <p className="pp-auth-badge__quote">
        {quote ? `"${quote}"` : "The posting does not mention work authorization."}
      </p>
    </div>
  );
}

function SkillList({ label, skills, tone }) {
  if (!skills || skills.length === 0) return null;
  return (
    <div className="pp-field-group">
      <span className="pp-field-label">{label}</span>
      <div className="pp-tag-row">
        {skills.map((s) => (
          <span key={s} className={`pp-tag pp-tag--${tone}`}>{s}</span>
        ))}
      </div>
    </div>
  );
}

export default function JdPanel({ breakdown }) {
  if (!breakdown) {
    return (
      <section className="pp-jd-panel pp-jd-panel--empty">
        <h2>Job description breakdown</h2>
        <p className="pp-muted">
          Paste a job posting in the chat and I'll break it down here.
        </p>
      </section>
    );
  }

  const {
    company,
    role,
    must_have_skills,
    nice_to_have_skills,
    red_flags,
    work_authorization,
    work_authorization_quote,
  } = breakdown;

  return (
    <section className="pp-jd-panel">
      <div className="pp-jd-panel__head">
        <h2>Job description breakdown</h2>
        <span className="pp-pill pp-pill--grey">from analyze_job_description</span>
      </div>

      <div className="pp-field-grid">
        <div className="pp-field-group">
          <span className="pp-field-label">Company</span>
          <span className="pp-field-value">{company || "-"}</span>
        </div>
        <div className="pp-field-group">
          <span className="pp-field-label">Role</span>
          <span className="pp-field-value">{role || "-"}</span>
        </div>
      </div>

      <AuthBadge status={work_authorization} quote={work_authorization_quote} />

      <SkillList label="Must-have skills" skills={must_have_skills} tone="green" />
      <SkillList label="Nice-to-have" skills={nice_to_have_skills} tone="grey" />

      {red_flags && red_flags.length > 0 && (
        <div className="pp-field-group">
          <span className="pp-field-label">Red flags</span>
          <ul className="pp-flag-list">
            {red_flags.map((flag, i) => (
              <li key={i}>{flag}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
