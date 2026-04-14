import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [react()],
    build: {
      outDir: "../static",
      emptyOutDir: true,
      rollupOptions: {
        output: {
          entryFileNames: "assets/index.js",
          chunkFileNames: "assets/[name].js",
          assetFileNames: "assets/[name][extname]",
        },
      },
    },
    server: {
      port: 5173,
      proxy: {
        "/api/meta": {
          target: env.VITE_ATLAN_BASE_URL || "https://localhost",
          changeOrigin: true,
          secure: false,
        },
      },
    },
  };
});
