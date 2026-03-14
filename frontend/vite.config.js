import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ command }) => ({
  plugins: [react()],

  server: {
    host: '0.0.0.0',
    port: 3000,
    // Proxy API calls in dev so VITE_API_URL is not needed locally.
    // The browser never sees http://backend:8000 — Vite forwards it server-side.
    proxy: {
      '/auth': 'http://localhost:8000',
      '/voice': 'http://localhost:8000',
      '/forms': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
    watch: {
      // usePolling only needed inside Docker on some Linux hosts
      usePolling: process.env.DOCKER === 'true',
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: false,   // No source maps in production build
    minify: 'esbuild',
  },
}))
