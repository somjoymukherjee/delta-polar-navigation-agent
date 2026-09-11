/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        polar: {
          950: '#030712',
          900: '#060b14',
          850: '#0a1120',
          800: '#0e172a',
          750: '#142038',
          700: '#1e293b',
          600: '#334155',
          cyan: '#00f0ff',
          ice: '#e0f2fe',
          frost: '#7dd3fc',
          accent: '#38bdf8'
        }
      },
      fontFamily: {
        sans: ['"Space Grotesk"', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      }
    },
  },
  plugins: [],
}
