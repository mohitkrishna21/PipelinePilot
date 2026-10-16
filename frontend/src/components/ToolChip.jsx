// A small pill shown while a tool call is in flight, or once it has a result.
export default function ToolChip({ name, resultSummary }) {
  return (
    <div className="pp-tool-chip">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#0B7A66"
           strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M5 12l5 5 9-10" />
      </svg>
      <span className="pp-mono">{name}</span>
      {resultSummary && <span className="pp-tool-chip__result">{resultSummary}</span>}
    </div>
  );
}
