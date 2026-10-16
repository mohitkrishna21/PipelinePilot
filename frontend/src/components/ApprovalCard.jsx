import { useEffect, useState } from "react";
import { APPROVAL_COUNTDOWN_SECONDS } from "../config.js";

function formatSeconds(total) {
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

// request: { tool_name, arguments } - arguments is whatever object the
// server sent; we print it as key: value lines.
export default function ApprovalCard({ request, onApprove, onReject }) {
  const [secondsLeft, setSecondsLeft] = useState(APPROVAL_COUNTDOWN_SECONDS);

  useEffect(() => {
    setSecondsLeft(APPROVAL_COUNTDOWN_SECONDS);
    const id = setInterval(() => {
      setSecondsLeft((s) => (s > 0 ? s - 1 : 0));
    }, 1000);
    return () => clearInterval(id);
  }, [request]);

  const args = request.arguments && typeof request.arguments === "object"
    ? request.arguments
    : {};

  return (
    <div className="pp-approval-card">
      <div className="pp-approval-card__head">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#92400E"
             strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M12 3l9 16H3L12 3z" />
          <path d="M12 10v4M12 17v.5" />
        </svg>
        <span>Approval needed before I change your data</span>
      </div>

      <div className="pp-approval-card__body pp-mono">
        {request.tool_name}
        {Object.entries(args).map(([key, value]) => (
          <div key={key}>
            {key}: "{String(value)}"
          </div>
        ))}
      </div>

      <div className="pp-approval-card__actions">
        <button type="button" className="pp-btn pp-btn--primary" onClick={onApprove}>
          Approve
        </button>
        <button type="button" className="pp-btn pp-btn--ghost" onClick={onReject}>
          Reject
        </button>
        <span className="pp-approval-card__timer">
          Auto-rejects in <span className="pp-mono">{formatSeconds(secondsLeft)}</span>
        </span>
      </div>
    </div>
  );
}
