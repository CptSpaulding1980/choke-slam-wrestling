const slugify = require("@sindresorhus/slugify");
const markdownIt = require("markdown-it");
const fs = require("fs");
const matter = require("gray-matter");
const faviconsPlugin = require("eleventy-plugin-gen-favicons");
const tocPlugin = require("eleventy-plugin-nesting-toc");
const { parse } = require("node-html-parser");
const htmlMinifier = require("html-minifier-terser");
const pluginRss = require("@11ty/eleventy-plugin-rss");

const { headerToId, namedHeadingsFilter } = require("./src/helpers/utils");
const {
  userMarkdownSetup,
  userEleventySetup,
} = require("./src/helpers/userSetup");

const Image = require("@11ty/eleventy-img");
function transformImage(src, cls, alt, sizes, widths = ["500", "700", "auto"]) {
  let options = {
    widths: widths,
    formats: ["webp", "jpeg"],
    outputDir: "./dist/img/optimized",
    urlPath: "/img/optimized",
  };

  Image(src, options);
  let metadata = Image.statsSync(src, options);
  return metadata;
}

function getAnchorLink(filePath, linkTitle) {
  const {attributes, innerHTML} = getAnchorAttributes(filePath, linkTitle);
  return `<a ${Object.keys(attributes).map(key => `${key}="${attributes[key]}"`).join(" ")}>${innerHTML}</a>`;
}

function getAnchorAttributes(filePath, linkTitle) {
  let fileName = filePath.replaceAll("&amp;", "&");
  let header = "";
  let headerLinkPath = "";
  if (filePath.includes("#")) {
    [fileName, header] = filePath.split("#");
    headerLinkPath = `#${headerToId(header)}`;
  }

  let noteIcon = process.env.NOTE_ICON_DEFAULT;
  let permalink = `/notes/${slugify(filePath)}`;
  let deadLink = false;
  try {
    const startPath = "./src/site/notes/";
    const fullPath = fileName.endsWith(".md")
      ? `${startPath}${fileName}`
      : `${startPath}${fileName}.md`;
    const file = fs.readFileSync(fullPath, "utf8");
    const frontMatter = matter(file);
    if (frontMatter.data.permalink) {
      permalink = frontMatter.data.permalink;
    }
    if (
      frontMatter.data.tags &&
      frontMatter.data.tags.indexOf("gardenEntry") != -1
    ) {
      permalink = "/";
    }
    if (frontMatter.data.noteIcon) {
      noteIcon = frontMatter.data.noteIcon;
    }
  } catch {
    deadLink = true;
  }

  if (deadLink) {
    return {
      attributes: {
        "class": "internal-link is-unresolved",
        "href": "/404",
        "target": "",
      },
      innerHTML: linkTitle || fileName,
    }
  }
  return {
    attributes: {
      "class": "internal-link",
      "target": "",
      "data-note-icon": noteIcon,
      "href": `${permalink}${headerLinkPath}`,
    },
    innerHTML: linkTitle || fileName,
  }
}

const tagRegex = /(^|\s|\>)(#[^\s!@#$%^&*()=+\.,\[{\]};:'"?><]+)(?!([^<]*>))/g;

module.exports = function (eleventyConfig) {
  eleventyConfig.setLiquidOptions({ dynamicPartials: true });

  let markdownLib = markdownIt({
    breaks: true,
    html: true,
    linkify: true,
  })
    .use(require("markdown-it-anchor"), { slugify: headerToId })
    .use(require("markdown-it-mark"))
    .use(require("markdown-it-footnote"))
    .use(function (md) {
      md.renderer.rules.hashtag_open = function () {
        return '<a class="tag" onclick="toggleTagSearch(this)">';
      };
    })
    .use(require("markdown-it-mathjax3"), {
      tex: { inlineMath: [["$", "$"]] },
      options: { skipHtmlTags: { "[-]": ["pre"] } },
    })
    .use(require("markdown-it-attrs"))
    .use(require("markdown-it-task-checkbox"), {
      disabled: true,
      divWrap: false,
      divClass: "checkbox",
      idPrefix: "cbx_",
      ulClass: "task-list",
      liClass: "task-list-item",
    })
    .use(require("markdown-it-plantuml"), {
      openMarker: "```plantuml",
      closeMarker: "```",
    })
    .use(namedHeadingsFilter)
    .use(userMarkdownSetup);

  eleventyConfig.setLibrary("md", markdownLib);

  // Standard Filter
  eleventyConfig.addFilter("isoDate", date => date && date.toISOString());

  // feed.njk Filter
  eleventyConfig.addFilter("dateToRfc3339", date => {
    try { return new Date(date).toISOString(); } catch { return ""; }
  });

  eleventyConfig.addFilter("getNewestCollectionItemDate", (collection, prop = "date") => {
    if (!collection || !collection.length) return "";
    let newest = collection[0][prop];
    collection.forEach(item => {
      if (item[prop] && item[prop] > newest) newest = item[prop];
    });
    return newest;
  });

  // Markdown Links
  eleventyConfig.addFilter("link", str =>
    str &&
      str.replace(/\[\[(.*?\|.*?)\]\]/g, function (match, p1) {
        if (p1.indexOf("],[") > -1 || p1.indexOf('"$"') > -1) return match;
        const [fileLink, linkTitle] = p1.split("|");
        return getAnchorLink(fileLink, linkTitle);
      })
  );

  // Tags
  eleventyConfig.addFilter("taggify", str =>
    str &&
      str.replace(tagRegex, (match, precede, tag) =>
        `${precede}<a class="tag" onclick="toggleTagSearch(this)" data-content="${tag}">${tag}</a>`
      )
  );

  eleventyConfig.addFilter("searchableTags", str => {
    let tags;
    let match = str && str.match(tagRegex);
    if (match) tags = match.map(m => `"${m.split("#")[1]}"`).join(", ");
    return tags ? `${tags},` : "";
  });

  eleventyConfig.addFilter("hideDataview", str =>
    str && str.replace(/\(\S+\:\:(.*)\)/g, (_, value) => value.trim())
  );

  eleventyConfig.addFilter("jsonify", variable => JSON.stringify(variable) || '""');

  // Benutzerdefinierte Eleventy Setup Funktion
  userEleventySetup(eleventyConfig);

  return {
    dir: { input: "src/site", output: "dist", data: "_data" },
    templateFormats: ["njk", "md", "11ty.js"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: false,
    passthroughFileCopy: true,
  };
};
