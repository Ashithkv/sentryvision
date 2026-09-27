/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        void: "#0B0F13",
        panel: "#141B21",
        raised: "#1B242B",
        hairline: "#263039",
        ink: "#E8EDF1",
        muted: "#7C8994",
        signal: "#00D9A3",
        alert: "#FF5B4E",
        roi: "#FFC24B",
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
