/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0F172A",
        primary: "#6366F1",
        accent: "#22D3EE",
        text: "#E2E8F0",
        muted: "#64748B"
      }
    }
  }
}