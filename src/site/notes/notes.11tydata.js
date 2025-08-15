require("dotenv").config();
const settings = require("../../helpers/constants");
const allSettings = settings.ALL_NOTE_SETTINGS;

// notes.json einbinden
const notes = require("./notes.json"); // Pfad zu notes.json anpassen

module.exports = {
  eleventyComputed: {
    layout: (data) => {
      if (data.tags && data.tags.indexOf("gardenEntry") !== -1) {
        return "layouts/index.njk";
      }
      return "layouts/note.njk";
    },
    permalink: (data) => {
      if (data.tags && data.tags.indexOf("gardenEntry") !== -1) {
        return "/";
      }
      return data.permalink || undefined;
    },
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
  notes
};
