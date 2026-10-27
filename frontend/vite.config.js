import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy: /api/* on the frontend is forwarded to the FastAPI backend,
// so no CORS setup is needed while developing.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
