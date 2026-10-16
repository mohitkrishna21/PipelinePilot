import { useState } from "react";

const QUICK_ACTIONS = [
  "Show my pipeline",
  "Paste a job description",
  "Draft a follow-up",
];

export default function Composer({ disabled, disabledReason, onSend }) {
  const [value, setValue] = useState("");

  function submit() {
    const text = value.trim();
    if (!text || disabled) return;
    onSend(text);
    setValue("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="pp-composer">
      <div className="pp-composer__quick-actions">
        {QUICK_ACTIONS.map((label) => (
          <button
            key={label}
            type="button"
            className="pp-chip-btn"
            disabled={disabled}
            onClick={() => onSend(label)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="pp-composer__row">
        <label htmlFor="pp-message" className="pp-sr-only">Message</label>
        <textarea
          id="pp-message"
          rows={2}
          value={value}
          disabled={disabled}
          placeholder={disabled ? disabledReason : "Ask about your pipeline or paste a job description"}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          type="button"
          aria-label="Send"
          className="pp-send-btn"
          disabled={disabled || !value.trim()}
          onClick={submit}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF"
               strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M12 19V5M5 12l7-7 7 7" />
          </svg>
        </button>
      </div>

      <span className="pp-composer__footnote">
        Demo uses a shared OpenAI budget. Answers are checked against resume
        facts before they appear.
      </span>
    </div>
  );
}
