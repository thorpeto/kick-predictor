/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bundesliga': {
          'red': '#d20515',
          'dark': '#001e50',
        },
      },
    },
  },
  plugins: [],
}
