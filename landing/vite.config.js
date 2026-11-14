import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// `base: './'` keeps the built asset URLs relative, so the site works at a
// domain root or a subpath (Vercel, GitHub Pages) without extra config.
export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
