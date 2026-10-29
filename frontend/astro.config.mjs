import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  output: 'static',
  server: { host: '127.0.0.1', port: 4321 },
  vite: {
    plugins: [tailwindcss()],
    server: {
      strictPort: true,
      proxy: { '/api': 'http://127.0.0.1:8000', '/static': 'http://127.0.0.1:8000' },
    },
  },
});
