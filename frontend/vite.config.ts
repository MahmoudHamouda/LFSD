import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

// Load environment variables
export default defineConfig(({ mode }) => ({
  plugins: [react(), tsconfigPaths()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target:
          mode === "development"
            ? "http://localhost:5000" // Local backend for development
            : "http://34.171.220.94", // Google Cloud backend for production
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    outDir: "dist",
    sourcemap: mode === "production" ? false : true,
  },
}));
