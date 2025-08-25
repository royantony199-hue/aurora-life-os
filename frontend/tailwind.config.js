/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4A90E2',
        secondary: '#722ED1',
        success: '#52C41A',
        warning: '#FAAD14',
        destructive: '#FF4D4F',
        neutral: {
          900: '#262626',
          600: '#8C8C8C',
          300: '#D9D9D9',
        },
        background: '#F5F7FA',
      },
      borderRadius: {
        DEFAULT: '0.625rem',
      },
      fontSize: {
        base: '14px',
      },
    },
  },
  plugins: [],
}