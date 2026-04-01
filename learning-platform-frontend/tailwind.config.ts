import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./hooks/**/*.{js,ts,jsx,tsx,mdx}",
    "./services/**/*.{js,ts,jsx,tsx,mdx}",
    "./utils/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "rgb(var(--background) / <alpha-value>)",
        foreground: "rgb(var(--foreground) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        "surface-muted": "rgb(var(--surface-muted) / <alpha-value>)",
        border: "rgb(var(--border) / <alpha-value>)",
        brand: {
          50: "rgb(var(--brand-soft) / <alpha-value>)",
          100: "rgb(var(--brand-soft) / <alpha-value>)",
          200: "rgb(var(--brand-soft) / <alpha-value>)",
          300: "rgb(var(--brand-end) / <alpha-value>)",
          400: "rgb(var(--brand-end) / <alpha-value>)",
          500: "rgb(var(--brand-end) / <alpha-value>)",
          600: "rgb(var(--brand-start) / <alpha-value>)",
          700: "rgb(var(--brand-start) / <alpha-value>)",
          800: "rgb(var(--brand-start) / <alpha-value>)",
          900: "rgb(var(--brand-start) / <alpha-value>)",
        },
        accent: {
          cyan: "#06b6d4",
          emerald: "#10b981",
          amber: "#f59e0b",
          rose: "#f43f5e",
        },
      }
    },
    boxShadow: {
      glow: "0 24px 80px rgba(79, 70, 229, 0.18)",
      panel: "0 20px 60px rgba(15, 23, 42, 0.08)",
    },
    backgroundImage: {
      "grid-soft":
        "linear-gradient(to right, rgba(148,163,184,0.12) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.12) 1px, transparent 1px)",
    },
  },
  plugins: [],
};

export default config;
