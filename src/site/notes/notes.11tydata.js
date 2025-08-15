require("dotenv").config();
const settings = require("../../helpers/constants");
const allSettings = settings.ALL_NOTE_SETTINGS;

// notes.json einbinden
const notes = require("./notes.json");

module.exports = {
  eleventyComputed: {
    layout: (data) => "layouts/note.njk", // alle Notizen nutzen dasselbe Layout

    permalink: (data) => {
      if (data["dg-home"] === true) {
        return "/index.html"; // Home-Seite direkt im Root
      }
      return data.permalink || undefined;
    },

    settings: (data) => {
      const noteSettings = {};
      allSettings.forEach((setting) => {
        let noteSetting = data[setting];
        let globalSetting = process.env[setting];

        noteSettings[setting] =
          noteSetting || (globalSetting === "true" && noteSetting !== false);
      });
      return noteSettings;
    },
  },

  notes
};
