import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwind from "@tailwindcss/vite";

export default defineConfig({
  plugins: [
    react(),
    tailwind(),    // ← first‑party Vite plugin, no extra options needed
  ],
});
