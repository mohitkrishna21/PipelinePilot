import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import Dashboard from "./Dashboard.jsx";
import "./styles.css";

// No router dependency: the dashboard is one extra static page served by
// Nginx at /dashboard, so a plain path check is enough.
const page = window.location.pathname.startsWith("/dashboard") ? <Dashboard /> : <App />;

createRoot(document.getElementById("root")).render(
  <StrictMode>{page}</StrictMode>
);
