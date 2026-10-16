// extractPitchNote.js
//
// The Pitch Note isn't a separate field from the backend - it's prose the
// agent writes inline, in its chat reply, labeled with its own "Pitch
// Note:" line, followed later by a "Gaps:" line. Real output looks like:
//
//   Work authorization: ...
//   Quote: "..."
//
//   Pitch Note:
//   <4-5 sentence note>
//
//   Gaps: ...
//
//   <closing question>
//
// Anchoring on "Pitch Note:" itself (instead of guessing from the line
// before it) means whatever the agent prints ahead of that label -
// Company/Role/Must-have/Red flags/Work authorization/Quote, in whatever
// order - never leaks into the extracted note. This is best-effort: if the
// model's wording ever drifts and no "Pitch Note:" or "Gaps:" line appears,
// extraction just returns null and the chat bubble still displays the full
// text untouched - no regression, nothing hidden.
export function extractPitchNote(text) {
  if (!text) return null;

  const pitchMatch = text.match(/^Pitch Note:\s*/m);
  const gapsMatch = text.match(/^Gaps:.*$/m);

  if (!pitchMatch || !gapsMatch) return null;

  const noteStart = pitchMatch.index + pitchMatch[0].length;
  const noteEnd = gapsMatch.index;

  if (noteEnd <= noteStart) return null;

  const note = text.slice(noteStart, noteEnd).trim();
  const gaps = gapsMatch[0].replace(/^Gaps:\s*/, "").trim();

  if (!note) return null;

  return { note, gaps };
}