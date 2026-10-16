// All API calls go to the same origin under /api.
// In development, Vite proxies /api to the FastAPI backend (see vite.config.js).
// In production, Nginx proxies /api to the backend.
export const API_BASE = "/api";

// How long the approval card counts down before the server auto-rejects.
// Matches APPROVAL_TIMEOUT in web/app.py (120s), shown a touch shorter so the
// UI never claims time the server has already spent.
export const APPROVAL_COUNTDOWN_SECONDS = 118;

// How often the dashboard refreshes /metrics.
export const METRICS_POLL_MS = 5000;
