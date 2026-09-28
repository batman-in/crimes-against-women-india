import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // maplibre-gl 6 loads its worker via import.meta.url; pre-bundling breaks that path
  optimizeDeps: { exclude: ['maplibre-gl'] },
  worker: { format: 'es' },
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
