// useSession.js - keeps one session id per browser tab and closes it
// cleanly when the visitor leaves.
//
// Why sessionStorage and not localStorage: sessionStorage is cleared when
// the tab closes, which matches how the backend treats a session (it reaps
// idle ones anyway, but there is no reason to resurrect a dead session in a
// brand new tab).

import { useCallback, useEffect, useRef, useState } from "react";
import { closeSession } from "../api/client.js";

const STORAGE_KEY = "pp_session_id";

export function useSession() {
  const [sessionId, setSessionIdState] = useState(() => {
    try {
      return sessionStorage.getItem(STORAGE_KEY);
    } catch {
      return null;
    }
  });

  // Keep a ref in sync so the pagehide handler always sees the latest id
  // without needing to re-subscribe on every change.
  const sessionIdRef = useRef(sessionId);
  sessionIdRef.current = sessionId;

  const setSessionId = useCallback((id) => {
    setSessionIdState(id);
    try {
      if (id) {
        sessionStorage.setItem(STORAGE_KEY, id);
      } else {
        sessionStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // sessionStorage can throw in a locked-down browser; the app still
      // works, it just won't survive a reload.
    }
  }, []);

  // Start over: tell the server to close the old session, then forget it.
  const resetSession = useCallback(() => {
    closeSession(sessionIdRef.current);
    setSessionId(null);
  }, [setSessionId]);

  useEffect(() => {
    function handlePageHide() {
      closeSession(sessionIdRef.current);
    }

    window.addEventListener("pagehide", handlePageHide);
    return () => window.removeEventListener("pagehide", handlePageHide);
  }, []);

  return { sessionId, setSessionId, resetSession };
}
