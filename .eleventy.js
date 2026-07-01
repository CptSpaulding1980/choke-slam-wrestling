// Choke Slam Wrestling — simplified Eleventy config
// Site is pre-built in docs/ and served directly via GitHub Pages.
// This config is kept for reference; build.py handles the pipeline.

module.exports = function(eleventyConfig) {
  // Passthrough: serve static files from docs/
  eleventyConfig.setUseGitIgnore(false);

  return {
    dir: {
      input: "docs",
      output: "docs",
    },
    templateFormats: ["html", "njk", "md"],
    htmlTemplateEngine: false,
    markdownTemplateEngine: false,
  };
};
