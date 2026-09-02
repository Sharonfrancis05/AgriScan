import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#0f1613",
          raised: "#161f1b",
          border: "#26332c",
        },
        brand: {
          DEFAULT: "#3fb27f",
          light: "#6bd6a4",
          dark: "#2a8a63",
        },
        // Solid fills meant to be paired with white text + the severity name
        // as a visible label (never relied on as color-alone identity) —
        // each individually WCAG-AA verified for white-text contrast.
        severity: {
          healthy: "#15803d",
          mild: "#a16207",
          moderate: "#c2410c",
          severe: "#dc2626",
          critical: "#7f1d1d",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
