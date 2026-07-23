import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server runs on :5900 and proxies the API surface to the backend on :8900.
export default defineConfig({
  plugins: [react()],
  server: {
    // Served behind the nginx :85 reverse proxy and reachable via domain/IP/localhost.
    // Disable Vite's DNS-rebinding host guard accordingly.
    allowedHosts: true,
    port: 5900,
    proxy: {
      "/api": { target: "http://localhost:8900", changeOrigin: true },
      "/health": { target: "http://localhost:8900", changeOrigin: true },
    },
  },
  build: {
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom"],
        },
      },
    },
  },
});
