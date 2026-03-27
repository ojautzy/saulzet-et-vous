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
      typography: {
        DEFAULT: {
          css: {
            "--tw-prose-body": "#1A1A18",
            "--tw-prose-headings": "#2D5016",
            "--tw-prose-links": "#2D5016",
            "--tw-prose-bold": "#1A1A18",
            "--tw-prose-counters": "#6B6560",
            "--tw-prose-bullets": "#4A7C28",
            "--tw-prose-hr": "#F5EDE0",
            "--tw-prose-quotes": "#2D5016",
            "--tw-prose-quote-borders": "#4A7C28",
            "--tw-prose-captions": "#6B6560",
            "--tw-prose-th-borders": "#F5EDE0",
            "--tw-prose-td-borders": "#F5EDE0",
            "h1, h2, h3": {
              fontFamily: '"Playfair Display", serif',
            },
            a: {
              textDecoration: "underline",
              textUnderlineOffset: "2px",
              "&:hover": {
                color: "#4A7C28",
              },
            },
          },
        },
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
  plugins: [require("@tailwindcss/typography"), require("daisyui")],
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
