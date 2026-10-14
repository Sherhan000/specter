import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const t = 'http://localhost:3000'

export default defineConfig({
  root: 'client',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': t,
      '/f': t,
      '/socket.io': { target: t, ws: true }
    }
  },
  build: { outDir: 'dist', emptyOutDir: true }
})
