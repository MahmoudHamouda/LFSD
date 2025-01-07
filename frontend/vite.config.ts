import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  build: {
    rollupOptions: {
      external: ["@fluentui/react-icons"], // Treat as external
    },
  },
  server: {
    port: 3000,
  },
});
