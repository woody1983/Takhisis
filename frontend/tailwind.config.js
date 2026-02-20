/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'lily': {
          'dew': '#F4FFE0',
          'spring': '#C6EF7E',
          'vibrant': '#18A518',
          'moss': '#19C519',
          'forest': '#0C7A0C',
        }
      },
      borderRadius: {
        'squircle': '24px',
        'squircle-lg': '32px',
      },
      boxShadow: {
        'soft': '0 4px 20px -2px rgba(12, 122, 12, 0.1)',
        'soft-lg': '0 8px 30px -4px rgba(12, 122, 12, 0.15)',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.07)',
      },
      backdropBlur: {
        'glass': '8px',
      }
    },
  },
  plugins: [],
}
