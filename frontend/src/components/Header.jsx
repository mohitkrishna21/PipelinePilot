export default function Header({ turnsUsed, maxTurns, onNewSession }) {
  return (
    <header className="pp-header">
      <div className="brand">
        <svg width="24" height="24" viewBox="0 0 24 24" aria-label="PipelinePilot" role="img">
          <path fill="#f97316" d="M3 11.5 21 3l-8.5 18-2.2-7.3z" />
        </svg>
        <span>PipelinePilot</span>
      </div>

      <span className="pp-pill pp-pill--teal">Live demo - sample data</span>

      <div className="pp-header__spacer" />

      {maxTurns != null && (
        <span className="pp-header__stat">
          Turns used <span className="pp-mono">{turnsUsed} / {maxTurns}</span>
        </span>
      )}
      <span className="pp-header__stat pp-header__stat--muted">
        Session resets after idle
      </span>

      <button type="button" className="pp-btn pp-btn--ghost" onClick={onNewSession}>
        New session
      </button>
    </header>
  );
}
