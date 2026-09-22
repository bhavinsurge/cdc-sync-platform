import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          ink: "#0f172a",
          mist: "#64748b",
          soft: "#f1f5f9",
          line: "#e2e8f0",
        },
        river: {
          50: "#eef8fc",
          100: "#d5eef8",
          400: "#38bdf0",
          500: "#0ba5d4",
          600: "#0284c7",
          700: "#0369a1",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "river-wash":
          "radial-gradient(1200px 600px at 10% -10%, rgba(11,165,212,0.18), transparent 55%), radial-gradient(900px 500px at 100% 0%, rgba(2,132,199,0.12), transparent 50%), linear-gradient(180deg, #f8fafc 0%, #eef4f8 45%, #f8fafc 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
