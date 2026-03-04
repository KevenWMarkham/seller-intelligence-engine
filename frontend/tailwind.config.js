/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        nexus: {
          blue: "#1a56db",
          dark: "#111827",
          surface: "#1f2937",
          border: "#374151",
        },
      },
    },
  },
  plugins: [],
};
