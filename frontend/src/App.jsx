import { useEffect, useRef, useState } from "react";
import Header from "./components/Header.jsx";
import PipelineSidebar from "./components/PipelineSidebar.jsx";
import ChatMessage from "./components/ChatMessage.jsx";
import ApprovalCard from "./components/ApprovalCard.jsx";
import JdPanel from "./components/JdPanel.jsx";
import PitchNote from "./components/PitchNote.jsx";
import Composer from "./components/Composer.jsx";
import { useSession } from "./hooks/useSession.js";
import { sendChat, sendApproval, fetchPipeline } from "./api/client.js";
import { extractPitchNote } from "./lib/extractPitchNote.js";

let nextId = 1;
function makeId() {
  return nextId++;
}

export default function App() {
  const { sessionId, setSessionId, resetSession } = useSession();

  const [messages, setMessages] = useState([]);
  const [jdBreakdown, setJdBreakdown] = useState(null);
  const [pitchNote, setPitchNote] = useState(null);
  const [pendingApproval, setPendingApproval] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [turnsUsed, setTurnsUsed] = useState(0);

  const [applications, setApplications] = useState([]);
  const [pipelineLoading, setPipelineLoading] = useState(true);
  const [pipelineError, setPipelineError] = useState(false);

  // Points at the in-progress assistant message while a turn streams in.
  const pendingTurnRef = useRef(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    fetchPipeline()
      .then((body) => setApplications(body.applications ?? []))
      .catch(() => setPipelineError(true))
      .finally(() => setPipelineLoading(false));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, pendingApproval]);

  function appendMessage(entry) {
    setMessages((prev) => [...prev, { id: makeId(), ...entry }]);
  }

  function startTurn() {
    // The id must be assigned here, up front, and used for both the
    // in-flight ref and the list entry. If the two ever end up with
    // different ids, updatePendingTurn's lookup below silently matches
    // nothing and every later SSE event (tool calls, the final answer)
    // gets dropped on the floor.
    const turn = { id: makeId(), role: "assistant", text: "", tools: [], guardrailKind: null };
    pendingTurnRef.current = turn;
    setMessages((prev) => [...prev, turn]);
  }

  function updatePendingTurn(patch) {
    const turn = pendingTurnRef.current;
    if (!turn) return;
    Object.assign(turn, patch);
    setMessages((prev) => prev.map((m) => (m.id === turn.id ? { ...m, ...patch } : m)));
  }

  function finalizePendingTurn() {
    pendingTurnRef.current = null;
    setTurnsUsed((n) => n + 1);
  }

  async function handleSend(text) {
    appendMessage({ role: "user", text });
    startTurn();
    setIsStreaming(true);

    // Assigned on the first "session" event for a brand-new session.
    let receivedSessionId = sessionId;

    await sendChat({
      message: text,
      sessionId,
      handlers: {
        onSession: (data) => {
          receivedSessionId = data.session_id;
          if (data.session_id !== sessionId) setSessionId(data.session_id);
        },

        onToolCall: (data) => {
          const turn = pendingTurnRef.current;
          if (!turn) return;
          turn.tools = [...turn.tools, { name: data.name, resultSummary: null }];
          updatePendingTurn({ tools: turn.tools });
        },

        onToolResult: (data) => {
          const turn = pendingTurnRef.current;
          if (!turn) return;
          // Match the most recent tool call of this name that has no result yet.
          const tools = [...turn.tools];
          for (let i = tools.length - 1; i >= 0; i--) {
            if (tools[i].name === data.name && !tools[i].resultSummary) {
              tools[i] = { ...tools[i], resultSummary: summarizeResult(data.output) };
              break;
            }
          }
          turn.tools = tools;
          updatePendingTurn({ tools });
        },

        onJdBreakdown: (data) => {
          setJdBreakdown(data);
        },

        onApprovalRequired: (data) => {
          setPendingApproval({ ...data, sessionId: receivedSessionId });
        },

        onGuardrail: (data) => {
          updatePendingTurn({ role: "guardrail", guardrailKind: data.kind });
        },

        onFinal: (data) => {
          updatePendingTurn({ text: data.text });
          // Best-effort: only a clean reply (never a guardrail block) can
          // contain a real Pitch Note, and extraction itself returns null
          // on anything that doesn't match the labeled format - so a plain
          // "no note this turn" reply just leaves the sidebar unchanged.
          const extracted = extractPitchNote(data.text);
          if (extracted) setPitchNote(extracted);
          finalizePendingTurn();
        },

        onError: (data) => {
          const turn = pendingTurnRef.current;
          if (turn) {
            updatePendingTurn({ role: "error", text: data.message });
          } else {
            appendMessage({ role: "error", text: data.message, tools: [] });
          }
          pendingTurnRef.current = null;
        },
      },
    });

    setIsStreaming(false);
  }

  async function handleApprove() {
    if (!pendingApproval) return;
    const ok = await sendApproval({ sessionId: pendingApproval.sessionId, approved: true });
    setPendingApproval(null);
    if (!ok) {
      appendMessage({ role: "error", text: "Could not record your approval. Please try again.", tools: [] });
    }
  }

  async function handleReject() {
    if (!pendingApproval) return;
    const ok = await sendApproval({ sessionId: pendingApproval.sessionId, approved: false });
    setPendingApproval(null);
    if (!ok) {
      appendMessage({ role: "error", text: "Could not record your rejection. Please try again.", tools: [] });
    }
  }

  function handleNewSession() {
    resetSession();
    setMessages([]);
    setJdBreakdown(null);
    setPitchNote(null);
    setPendingApproval(null);
    setTurnsUsed(0);
    pendingTurnRef.current = null;
  }

  const composerDisabled = isStreaming || !!pendingApproval;
  const composerReason = pendingApproval
    ? "Reply to approve or reject above first"
    : "Waiting for a reply...";

  return (
    <div className="pp-app">
      <Header turnsUsed={turnsUsed} maxTurns={null} onNewSession={handleNewSession} />

      <div className="pp-layout">
        <PipelineSidebar applications={applications} loading={pipelineLoading} error={pipelineError} />

        <main className="pp-main">
          <div className="pp-chat-scroll" ref={scrollRef}>
            <div className="pp-chat-inner">
              {messages.map((m) => (
                <ChatMessage key={m.id} role={m.role} text={m.text} tools={m.tools} />
              ))}

              {pendingApproval && (
                <ApprovalCard
                  request={pendingApproval}
                  onApprove={handleApprove}
                  onReject={handleReject}
                />
              )}
            </div>
          </div>

          <div className="pp-composer-wrap">
            <Composer
              disabled={composerDisabled}
              disabledReason={composerReason}
              onSend={handleSend}
            />
          </div>
        </main>

        <aside className="pp-inspector">
          <JdPanel breakdown={jdBreakdown} />
          <PitchNote note={pitchNote?.note} gaps={pitchNote?.gaps} />
        </aside>
      </div>
    </div>
  );
}

function summarizeResult(output) {
  if (output == null) return null;
  const text = typeof output === "string" ? output : JSON.stringify(output);
  if (Array.isArray(output)) return `${output.length} results`;
  return text.length > 40 ? `${text.slice(0, 40)}...` : text;
}