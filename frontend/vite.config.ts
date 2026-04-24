import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Sweet Neighbors Club',
        short_name: 'SNC',
        description: 'Риелторские уведомления',
        theme_color: '#ffffff',
        icons: [
          {
            src: '/1.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/2.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}']
      }
    })
  ]
});