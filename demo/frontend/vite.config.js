import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 백엔드(app/config.py)의 CORS_ORIGINS 기본값이 localhost:3000을 허용하도록
// 되어 있어서, 개발 서버 포트를 3000으로 고정한다.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
});
