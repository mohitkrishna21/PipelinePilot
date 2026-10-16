import { useEffect, useRef, useState } from "react";

// Shown in the right sidebar once the agent has drafted a Pitch Note for
// the most recent JD. `note` and `gaps` both come from extractPitchNote.js,
// which pulls them out of the agent's chat reply text - there's no
// separate backend field for either. Like JdPanel, this always shows the
// latest one; it's replaced, not appended, each time a new clean reply
// comes back.
export default function PitchNote({ note, gaps }) {
  const [copied, setCopied] = useState(false);
  const resetTimerRef = useRef(null);

  // Clear any pending revert-to-"Copy note" timer on unmount, so it never
  // fires setState after this panel is gone (e.g. a brand new session).
  useEffect(() => {
    return () => {
      if (resetTimerRef.current) clearTimeout(resetTimerRef.current);
    };
  }, []);

  if (!note) return null;

  function handleCopy() {
    navigator.clipboard?.writeText(note)
      .then(() => {
        setCopied(true);
        if (resetTimerRef.current) clearTimeout(resetTimerRef.current);
        resetTimerRef.current = setTimeout(() => setCopied(false), 1500);
      })
      .catch(() => {});
  }

  return (
    <section className="pp-pitch-note">
      <div className="pp-pitch-note__head">
        <h2>Pitch Note</h2>
        <span className="pp-pill pp-pill--teal-soft">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#0B7A66"
               strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M5 12l5 5 9-10" />
          </svg>
          Claims verified
        </span>
      </div>
      <div className="pp-pitch-note__body">
        {note.split("\n\n").map((para, i) => (
          <p key={i}>{para}</p>
        ))}
        {gaps && (
          <p>
            <strong>Gaps:</strong> {gaps}
          </p>
        )}
      </div>
      <button
        type="button"
        className={`pp-btn ${copied ? "pp-btn--copied" : "pp-btn--ghost"}`}
        onClick={handleCopy}
      >
        {copied ? "Copied" : "Copy note"}
      </button>
    </section>
  );
}