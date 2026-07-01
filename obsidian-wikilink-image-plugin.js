// obsidian-wikilink-image-plugin.js
module.exports = function markdownItObsidianWikilink(md) {
  const imageWikilinkRegex = /!\[\[([^\]]+?)\]\]/g;

  const defaultRender = md.renderer.rules.text || ((tokens, idx, options, env, self) =>
    self.renderToken(tokens, idx, options));

  md.renderer.rules.text = function (tokens, idx, options, env, self) {
    let content = tokens[idx].content;

    content = content.replace(imageWikilinkRegex, (match, p1) => {
      const imageName = p1.trim();
      const imagePath = `/img/user/z_Images/${imageName}`;
      return `<img src="${imagePath}" alt="${imageName}" loading="lazy">`;
    });

    tokens[idx].content = content;
    return defaultRender(tokens, idx, options, env, self);
  };
};
