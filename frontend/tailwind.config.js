/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: "#212121",
        panel: "#171717",
        border: {
          DEFAULT: "rgba(255, 255, 255, 0.10)",
          strong: "rgba(255, 255, 255, 0.16)",
        },
        heading: "#ECECEC",
        body: "#D1D1D1",
        "body-muted": "#B5B5B5",
        muted: "#9B9B9B",
      },
    },
  },
  plugins: [],
};
