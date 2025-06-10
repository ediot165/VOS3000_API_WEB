import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // expose env vars starting with VOS_ to the client
  envPrefix: ['VOS_'],
})
