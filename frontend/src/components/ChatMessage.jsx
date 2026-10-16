import ToolChip from "./ToolChip.jsx";

// Minimal markdown: turns **bold** into real <strong> text. Line breaks are
// handled separately, in CSS (white-space: pre-wrap on .pp-bubble), so a
// plain model answer with \n between list items already displays correctly
// without needing a full markdown library.
function renderInlineMarkdown(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**")
      ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part
  );
}

const BUBBLE_CLASS = {
  user: "pp-bubble--user",
  assistant: "pp-bubble--assistant",
  guardrail: "pp-bubble--guardrail",
  error: "pp-bubble--error",
};

// One turn. `tools` (assistant/guardrail turns only) is an array of
// {name, resultSummary} in the order the server emitted them.
export default function ChatMessage({ role, text, tools }) {
  if (role === "user") {
    return <div className="pp-bubble pp-bubble--user">{text}</div>;
  }

  return (
    <div className="pp-assistant-turn">
      {tools && tools.length > 0 && (
        <div className="pp-assistant-turn__tools">
          {tools.map((t, i) => (
            <ToolChip key={i} name={t.name} resultSummary={t.resultSummary} />
          ))}
        </div>
      )}
      {text && (
        <div className={`pp-bubble ${BUBBLE_CLASS[role] ?? BUBBLE_CLASS.assistant}`}>
          {role === "guardrail" && <strong>Held back: </strong>}
          {renderInlineMarkdown(text)}
        </div>
      )}
    </div>
  );
}