/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        playfair: ['"Playfair Display"', "serif"],
        sans: ['"Source Sans 3"', "system-ui", "sans-serif"],
        serif: ['"Source Serif 4"', "Georgia", "serif"],
      },
      colors: {
        "vert-foret": "#2D5016",
        "vert-prairie": "#4A7C28",
        "vert-clair": "#7BAE4E",
        "vert-tres-clair": "#E8F3DC",
        terre: "#8B6914",
        "terre-claire": "#C49A2A",
        creme: "#FDF8F0",
        "creme-fonce": "#F5EDE0",
        "gris-pierre": "#6B6560",
        "gris-clair": "#9B9590",
        encre: "#1A1A18",
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        saulzet: {
          primary: "#2D5016",
          "primary-content": "#FFFFFF",
          secondary: "#8B6914",
          "secondary-content": "#FFFFFF",
          accent: "#C49A2A",
          "accent-content": "#FFFFFF",
          neutral: "#6B6560",
          "neutral-content": "#FFFFFF",
          "base-100": "#FFFFFF",
          "base-200": "#FDF8F0",
          "base-300": "#F5EDE0",
          "base-content": "#1A1A18",
          info: "#4A7C28",
          success: "#7BAE4E",
          warning: "#C49A2A",
          error: "#DC2626",
        },
      },
    ],
  },
};
