/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0a0e17',
        'bg-secondary': '#111827',
        'bg-tertiary': '#1e293b',
        'bg-hover': '#273548',
        'border-color': '#2a3a50',
        'text-primary': '#e2e8f0',
        'text-secondary': '#94a3b8',
        'text-tertiary': '#64748b',
        'status-running': '#22c55e',
        'status-completed': '#3b82f6',
        'status-failed': '#ef4444',
        'status-warning': '#f59e0b',
        'status-queued': '#8b5cf6',
        'status-canceled': '#6b7280',
        'status-suspended': '#06b6d4',
        accent: '#3b82f6',
        'accent-hover': '#2563eb',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'IBM Plex Mono', 'monospace'],
        sans: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
};
