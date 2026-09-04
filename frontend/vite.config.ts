import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  return {
    plugins: [react()],
    server: {
      proxy: {
        "/api": env.DIG_BACKEND_URL ?? "http://127.0.0.1:18000",
      },
    },
    test: {
      environment: "jsdom",
      setupFiles: "./src/test-setup.ts",
      pool: "threads",
      testTimeout: 20000,
    },
  };
});
