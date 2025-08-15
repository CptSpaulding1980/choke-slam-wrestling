require("dotenv").config();
const notes = require("./notes.json"); // Pfad zu notes.json anpassen

module.exports = {
  eleventyComputed: {
    // Layout nur als Fallback
    layout: (data) => {
      // Home-Seite: rendere direkt
      if (data["dg-home"] === true) {
        return null; // kein Layout nötig
      }
      // Alle anderen Notizen: einfacher Markdown-Fallback
      return null;
    },

    // Permalink setzen
    permalink: (data) => {
      if (data["dg-home"] === true) {
        return "/index.html"; // Home-Seite als Root
      }
      return data.permalink || undefined;
    },
  },

  // Alle Notizen aus notes.json verfügbar
  notes
};
