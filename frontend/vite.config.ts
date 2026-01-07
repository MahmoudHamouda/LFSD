import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  base: "/LFSD/",
  build: {
    outDir: "dist",
    sourcemap: true,
  },
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/history': 'https://lfsd-backend-692544481281.us-central1.run.app',
      '/conversation': 'https://lfsd-backend-692544481281.us-central1.run.app',
      '/.auth': 'https://lfsd-backend-692544481281.us-central1.run.app',
      '/frontend_settings': 'https://lfsd-backend-692544481281.us-central1.run.app',
      '/api': {
        target: 'https://lfsd-backend-692544481281.us-central1.run.app',
        changeOrigin: true,
        secure: false,
        timeout: 300000,
        proxyTimeout: 300000,
      },
      '/user': 'https://lfsd-backend-692544481281.us-central1.run.app',
    },
  },
});
