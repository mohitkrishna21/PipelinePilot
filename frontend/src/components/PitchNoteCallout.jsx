// A highlighted block for one turn's Pitch Note, pulled out of the chat
// reply by extractPitchNote.js. Stays attached to the message it came from,
// so it scrolls with the conversation and never gets overwritten by a
// later JD like a single persistent panel would.
export default function PitchNoteCallout({ note, gaps }) {
  function handleCopy() {
    navigator.clipboard?.writeText(note).catch(() => {});
  }

  return (
    <div className="pp-pitch-callout">
      <div className="pp-pitch-callout__head">
        <span className="pp-pitch-callout__title">Pitch Note</span>
        <span className="pp-pill pp-pill--teal-soft">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#0B7A66"
               strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 12l5 5 9-10" />
          </svg>
          Claims verified
        </span>
      </div>

      <p className="pp-pitch-callout__body">{note}</p>

      {gaps && (
        <p className="pp-pitch-callout__gaps">
          <strong>Gaps:</strong> {gaps}
        </p>
      )}

      <button type="button" className="pp-btn pp-btn--ghost" onClick={handleCopy}>
        Copy note
      </button>
    </div>
  );
}
