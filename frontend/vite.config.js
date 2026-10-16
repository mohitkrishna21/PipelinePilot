import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During `npm run dev`, the browser talks to Vite on :5173. Any request to
// /api is forwarded to FastAPI on :8001 so the frontend code never needs to
// know the backend's real port - the same /api path works in production
// once Nginx takes over that forwarding job.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
