import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  build: {
    outDir: "dist",
    sourcemap: true,
  },
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/history': 'http://127.0.0.1:8003',
      '/conversation': 'http://127.0.0.1:8003',
      '/.auth': 'http://127.0.0.1:8003',
      '/frontend_settings': 'http://127.0.0.1:8003',
      '/api': {
        target: 'http://127.0.0.1:8003',
        changeOrigin: true,
        secure: false,
        timeout: 300000, // 5 minutes
        proxyTimeout: 300000,
      },
      '/user': 'http://127.0.0.1:8003',
    },
  },
});
