const { collect } = require('../../helpers/cswTitleCollectors');

// Recomputed on every build from the generated Championship notes.
module.exports = () => collect('src/site/notes');
