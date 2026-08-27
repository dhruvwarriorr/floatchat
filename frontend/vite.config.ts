import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const apiProxy = {
  "/chat": "http://127.0.0.1:8000",
  "/health": "http://127.0.0.1:8000",
};

export default defineConfig({
  plugins: [react()],
  server: { port: 3000, proxy: apiProxy },
  preview: { port: 3000, proxy: apiProxy },
});
