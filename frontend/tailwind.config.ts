import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        body: ['var(--font-body)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'Georgia', 'serif'],
      },
      colors: {
        accent: {
          DEFAULT: '#0d9488',
          light: '#14b8a6',
          dark: '#0f766e',
          subtle: '#f0fdfa',
        },
      },
      gridTemplateColumns: {
        '13': 'repeat(13, minmax(0, 1fr))',
      },
      keyframes: {
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.4s ease-out forwards',
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};
export default config;
