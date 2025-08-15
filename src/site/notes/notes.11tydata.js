require("dotenv").config();
const settings = require("../../helpers/constants");
const allSettings = settings.ALL_NOTE_SETTINGS;

// notes.json einbinden
const notes = require("./notes.json"); // Pfad zu notes.json anpassen

module.exports = {
  eleventyComputed: {
    layout: data => "layouts/note.njk",
    permalink: data => (data["dg-home"] === true ? "/" : data.permalink),
    settings: data => {
      const noteSettings = {};
      allSettings.forEach(setting => {
        const noteSetting = data[setting];
        const globalSetting = process.env[setting];
        noteSettings[setting] =
          noteSetting || (globalSetting === "true" && noteSetting !== false);
      });
      return noteSettings;
    },
  },
  notes
};
