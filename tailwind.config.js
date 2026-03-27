/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#e6f0ff',
          100: '#cce1ff',
          200: '#99c3ff',
          300: '#66a5ff',
          400: '#3387ff',
          500: '#0069ff',
          600: '#0054cc',
          700: '#003f99',
          800: '#002a66',
          900: '#001533',
        },
      },
    },
  },
  plugins: [],
}
