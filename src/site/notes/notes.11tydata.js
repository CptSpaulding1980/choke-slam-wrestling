require("dotenv").config();
const settings = require("../../helpers/constants");
const allSettings = settings.ALL_NOTE_SETTINGS;

// notes.json einbinden
const notes = require("./notes.json");

module.exports = {
  eleventyComputed: {
    layout: (data) => {
      // Home-Seite erkennt DG automatisch
      return "layouts/note.njk"; // für alle Notes
    },

    // Permalink setzen
    permalink: (data) => {
      if (data["dg-home"] === true) {
        return "/index.html"; // Home direkt ins Root
      }
      // Andere Notizen bleiben unter /notes/ oder ihrem eigenen Pfad
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
