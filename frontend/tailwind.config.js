/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0fdf4",
          100: "#dcfce7",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
        },
        cyan: {
          400: "#22d3ee",
          500: "#06b6d4",
          900: "#164e63",
        },
        soc: {
          dark: "#0a0f1d",
          panel: "#111827",
          border: "#1f2937",
          hover: "#1f293d",
          accent: "#38bdf8",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(56, 189, 248, 0.15)",
        "glow-green": "0 0 20px rgba(16, 185, 129, 0.2)",
        "glow-red": "0 0 20px rgba(239, 68, 68, 0.2)",
        "glow-amber": "0 0 20px rgba(245, 158, 11, 0.2)",
      },
    },
  },
  plugins: [],
};
