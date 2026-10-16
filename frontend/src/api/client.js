// client.js - talks to the FastAPI backend.
//
// The /chat endpoint streams Server-Sent Events over a POST request. The
// browser's built-in EventSource only does GET, so we read the response body
// ourselves with a stream reader and parse the SSE frames by hand.
//
// Wire format (from web/sse.py):
//   event: <name>\n
//   data: <json>\n
//   \n                 <- blank line ends one frame
//
// Event names we handle: session, tool_call, tool_result, jd_breakdown,
// approval_required, guardrail, final, error.

import { API_BASE } from "../config.js";

// Turn one raw frame ("event: x\ndata: {...}") into { event, data }.
function parseFrame(frame) {
  let event = "message";
  const dataLines = [];

  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  let data = null;
  const raw = dataLines.join("\n");

  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch {
      data = raw;
    }
  }

  return { event, data };
}

// Map an event name to the matching callback in `handlers`.
function dispatch(event, data, handlers) {
  const map = {
    session: "onSession",
    tool_call: "onToolCall",
    tool_result: "onToolResult",
    jd_breakdown: "onJdBreakdown",
    approval_required: "onApprovalRequired",
    guardrail: "onGuardrail",
    final: "onFinal",
    error: "onError",
  };

  const name = map[event];
  if (name && typeof handlers[name] === "function") {
    handlers[name](data);
  }
}

// Pull a human-readable message out of a non-200 response.
async function readErrorDetail(res) {
  let detail = "Something went wrong. Please try again.";
  try {
    const body = await res.json();
    if (body && body.detail) {
      detail = body.detail;
    }
  } catch {
    // no JSON body; keep the default
  }
  return detail;
}

// Send one chat turn and stream its events into the handlers.
// Returns when the stream ends. Pass an AbortSignal to cancel.
export async function sendChat({ message, sessionId, signal, handlers = {} }) {
  let res;

  try {
    res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId ?? null }),
      signal,
    });
  } catch (err) {
    if (err.name === "AbortError") return;
    handlers.onError?.({ message: "Could not reach the server. Check your connection." });
    return;
  }

  if (!res.ok) {
    const detail = await readErrorDetail(res);
    handlers.onError?.({ message: detail, status: res.status });
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    let chunk;
    try {
      chunk = await reader.read();
    } catch (err) {
      if (err.name === "AbortError") return;
      handlers.onError?.({ message: "The connection dropped mid-reply." });
      return;
    }

    if (chunk.done) break;

    buffer += decoder.decode(chunk.value, { stream: true });

    // A frame ends at a blank line (\n\n).
    let sep;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);

      if (frame.trim()) {
        const { event, data } = parseFrame(frame);
        dispatch(event, data, handlers);
      }
    }
  }
}

// Resolve a pending approval. approved=true runs the tool, false rejects it.
export async function sendApproval({ sessionId, approved }) {
  try {
    const res = await fetch(`${API_BASE}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, approved }),
    });
    const body = await res.json();
    return body.resolved === true;
  } catch {
    return false;
  }
}

// Load the read-only pipeline for the sidebar.
export async function fetchPipeline() {
  const res = await fetch(`${API_BASE}/pipeline`);
  if (!res.ok) throw new Error(`pipeline ${res.status}`);
  return res.json();
}

// Load the metrics summary for the dashboard.
export async function fetchMetrics() {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error(`metrics ${res.status}`);
  return res.json();
}

// Close a session when the visitor leaves. Uses sendBeacon so it still goes
// out while the page is unloading; falls back to fetch with keepalive.
export function closeSession(sessionId) {
  if (!sessionId) return;

  const url = `${API_BASE}/session/close`;
  const payload = JSON.stringify({ session_id: sessionId });

  if (navigator.sendBeacon) {
    const blob = new Blob([payload], { type: "application/json" });
    navigator.sendBeacon(url, blob);
    return;
  }

  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
    keepalive: true,
  }).catch(() => {});
}
