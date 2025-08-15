require("dotenv").config();
const settings = require("../../helpers/constants");
const allSettings = settings.ALL_NOTE_SETTINGS;

// notes.json einbinden
const notes = require("./notes.json"); // Pfad zu notes.json anpassen

module.exports = {
  eleventyComputed: {
    // Layout festlegen
    layout: (data) => {
      // Home-Seite erkennt DG automatisch
      if (data["dg-home"] === true) {
        return "layouts/note.njk"; // index.njk nicht nötig
      }
      // Optional: gardenEntry-Tags (für andere DG-Notizen)
      if (data.tags && data.tags.indexOf("gardenEntry") !== -1) {
        return "layouts/note.njk";
      }
      return "layouts/note.njk";
    },

    // Permalink setzen
    permalink: (data) => {
      if (data["dg-home"] === true) {
        return "/"; // Home-Seite auf Root
      }
      return data.permalink || undefined;
    },

    // DG-Einstellungen laden
    settings: (data) => {
      const noteSettings = {};
      allSettings.forEach((setting) => {
        let noteSetting = data[setting];
        let globalSetting = process.env[setting];

        let settingValue =
          noteSetting || (globalSetting === "true" && noteSetting !== false);
        noteSettings[setting] = settingValue;
      });
      return noteSettings;
    },
  },

  // Alle Notizen aus notes.json verfügbar machen
  notes
};
