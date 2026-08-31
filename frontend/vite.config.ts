import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During dev, requests to /api are proxied to the FastAPI backend on :8000,
// so no CORS config is needed for the common single-machine demo setup.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
