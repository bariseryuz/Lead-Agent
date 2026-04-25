import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  preview: {
    allowedHosts: ['.up.railway.app', 'lead-agent-production-ef75.up.railway.app'],
  },
})