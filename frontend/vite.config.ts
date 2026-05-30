import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 1420,
    strictPort: true,
    /** 监听 0.0.0.0，同一 WiFi 下的手机可通过局域网 IP 访问 */
    host: true,
    open: "http://localhost:1420/",
    proxy: {
      "/api": {
        target: "http://127.0.0.1:18765",
        changeOrigin: true,
      },
      "/ws": {
        target: "http://127.0.0.1:18765",
        ws: true,
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 1420,
    strictPort: true,
    host: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:18765",
        changeOrigin: true,
      },
      "/ws": {
        target: "http://127.0.0.1:18765",
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
