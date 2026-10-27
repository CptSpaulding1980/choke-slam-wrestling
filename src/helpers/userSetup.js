function userMarkdownSetup(md) {
  // The md parameter stands for the markdown-it instance used throughout the site generator.
  // Feel free to add any plugin you want here instead of /.eleventy.js
}
function userEleventySetup(eleventyConfig) {
  const { sectionFor, headerFor, enhanceContent, displayTitle } = require('./cswDesign');
  const markdown = require('markdown-it')({ html: true });
  eleventyConfig.addFilter('cswSection', sectionFor);
  eleventyConfig.addFilter('cswHeader', headerFor);
  eleventyConfig.addFilter('cswContent', enhanceContent);
  eleventyConfig.addFilter('cswTitle', displayTitle);
  eleventyConfig.addFilter('cswMarkdown', value => markdown.render(value || ''));
  eleventyConfig.addTransform('cswWhitespace', (html, outputPath) =>
    outputPath?.endsWith('.html') ? html.replace(/[ \t]+$/gm, '') : html
  );
}
exports.userMarkdownSetup = userMarkdownSetup;
exports.userEleventySetup = userEleventySetup;
