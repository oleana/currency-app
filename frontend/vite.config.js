import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Все запросы /api/* уходят на FastAPI-бекенд
      '/api': 'http://localhost:8000',
    },
  },
})
