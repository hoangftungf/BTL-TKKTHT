/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f8fafc',    // slate-50
          100: '#f1f5f9',   // slate-100
          200: '#e2e8f0',   // slate-200
          300: '#cbd5e1',   // slate-300
          400: '#94a3b8',   // slate-400
          500: '#64748b',   // slate-500
          600: '#0f172a',   // slate-900 (Primary Brand Color)
          700: '#1e293b',   // slate-800 (Hover/Focus Color)
          800: '#334155',   // slate-700
          900: '#475569',   // slate-600
        },
        secondary: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        accent: {
          DEFAULT: '#38BDF8', // sky-400
          400: '#38BDF8',
        },
        surface: '#FFFFFF',
        'text-main': '#1E293B',
        'text-muted': '#64748B',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'custom-smooth': '0 10px 40px -10px rgba(0,0,0,0.04)',
      },
    },
  },
  plugins: [],
}
