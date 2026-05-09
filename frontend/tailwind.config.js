/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  corePlugins: {
    preflight: false,
  },
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter"', "system-ui", "Segoe UI", "Roboto", "sans-serif"],
      },
      colors: {
        /** AI Architect 稿：薄荷绿主色 + 深绿文字 + 浅灰绿画布 */
        arch: {
          canvas: "#F7F9F8",
          surface: "#ffffff",
          primary: "#00A67E",
          primaryDark: "#008f6c",
          ink: "#004D3D",
          muted: "#5c6f6c",
          border: "#d5e5df",
          think: "#ecf8f4",
          thinkBorder: "#b8e0d4",
          accentSoft: "#d4f0e8",
          observe: "#f6fbfa",
        },
      },
      boxShadow: {
        arch: "0 1px 2px rgba(0, 77, 61, 0.06), 0 2px 8px rgba(0, 77, 61, 0.04)",
        "arch-lg": "0 2px 8px rgba(0, 77, 61, 0.08), 0 8px 24px rgba(0, 77, 61, 0.06)",
      },
    },
  },
  plugins: [],
};
