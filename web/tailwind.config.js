/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter Variable"', "system-ui", "sans-serif"],
        display: ['"Plus Jakarta Sans Variable"', '"Inter Variable"', "sans-serif"],
      },
      colors: {
        ink: { 950: "#05070d", 900: "#0a0f1c", 850: "#0e1424", 800: "#121a2e", 700: "#1b2540" },
        brand: { 300: "#6ff2c8", 400: "#34e0b0", 500: "#14c497", 600: "#0aa07c" },
        sky2: { 400: "#5cc8ff", 500: "#2fb2f5" },
        risk: { low: "#34d399", mid: "#fbbf24", high: "#fb7185" },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(52,224,176,.25), 0 8px 40px -8px rgba(52,224,176,.35)",
        card: "0 1px 0 0 rgba(255,255,255,.04) inset, 0 20px 50px -20px rgba(0,0,0,.6)",
      },
      keyframes: {
        aurora: {
          "0%,100%": { transform: "translate3d(0,0,0) scale(1)" },
          "33%": { transform: "translate3d(4%,-6%,0) scale(1.08)" },
          "66%": { transform: "translate3d(-5%,4%,0) scale(.95)" },
        },
        shimmer: { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
        float: { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-10px)" } },
        pulseRing: { "0%": { transform: "scale(.9)", opacity: ".7" }, "100%": { transform: "scale(1.6)", opacity: "0" } },
        borderSpin: { to: { "--angle": "360deg" } },
      },
      animation: {
        aurora: "aurora 22s ease-in-out infinite",
        "aurora-slow": "aurora 34s ease-in-out infinite reverse",
        shimmer: "shimmer 2.4s linear infinite",
        float: "float 6s ease-in-out infinite",
        "pulse-ring": "pulseRing 1.8s cubic-bezier(.2,.6,.4,1) infinite",
      },
    },
  },
  plugins: [],
};
