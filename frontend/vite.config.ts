import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

/** Porta do uvicorn quando usas `make dev` (ex.: `PORT=8001 make dev`). */
const apiPort = process.env.VITE_API_PORT ?? '8000'
const apiTarget = `http://127.0.0.1:${apiPort}`

export default defineConfig(({ mode }) => ({
  plugins: [vue(), tailwindcss()],
  base: mode === 'production' ? '/static/dist/' : '/',
  build: {
    outDir: '../src/interfaces/static/dist',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': { target: apiTarget, changeOrigin: true },
    },
  },
}))
