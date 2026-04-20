/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Google AI Studio-ish dark palette
        canvas: {
          900: "#131314", // main bg
          850: "#1b1c1d", // sidebar bg
          800: "#1f2021", // cards / input bg
          700: "#2a2b2d", // hover
          600: "#3c4043", // borders
        },
        brand: {
          blue: "#8ab4f8",
          accent: "#a8c7fa",
        },
        muted: {
          fg: "#9aa0a6",
          fg2: "#bdc1c6",
        },
      },
      fontFamily: {
        sans: [
          "Google Sans",
          "Inter",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
