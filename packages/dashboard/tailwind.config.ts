import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        serif: ["Playfair Display", "serif"],
      },
      colors: {
        brand: {
          50: "#FDF7F5",
          100: "#FAEFEA",
          200: "#F2D8CD",
          300: "#EABFAB",
          400: "#D98E71",
          500: "#C65D3B",
          600: "#B24928",
          700: "#943B1E",
          800: "#7A321B",
          900: "#642B18",
        },
        surface: {
          bg: "#FAF9F7",
          sidebar: "#F2F0EB",
          card: "#FFFFFF",
          highlight: "#F5F3ED",
        },
      },
      boxShadow: {
        soft: "0 4px 20px -4px rgba(41, 37, 36, 0.05)",
        "sm-soft": "0 2px 10px -2px rgba(41, 37, 36, 0.03)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
