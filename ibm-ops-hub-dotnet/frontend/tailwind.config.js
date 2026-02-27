/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        'bg-primary':    'var(--bg-primary)',
        'bg-secondary':  'var(--bg-secondary)',
        'bg-hover':      'var(--bg-hover)',
        'border-color':  'var(--border-color)',
        'text-primary':  'var(--text-primary)',
        'text-secondary':'var(--text-secondary)',
        'text-tertiary': 'var(--text-tertiary)',
        'accent':        'var(--accent)',
        'status-running':   'var(--status-running)',
        'status-completed': 'var(--status-completed)',
        'status-failed':    'var(--status-failed)',
        'status-warning':   'var(--status-warning)',
        'status-unknown':   'var(--status-unknown)',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};
