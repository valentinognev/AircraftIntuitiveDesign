import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    proxy: {
      "/models": "http://127.0.0.1:8002",
      "/analyze": "http://127.0.0.1:8002",
      "/stability": "http://127.0.0.1:8002",
      "/control-derivatives": "http://127.0.0.1:8002",
    },
  },
  test: {
    include: ["src/**/*.test.ts"],
  },
});
