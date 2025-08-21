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
  const { attributes, innerHTML } = getAnchorAttributes(filePath, linkTitle);
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
  const title = linkTitle ? linkTitle : fileName;
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
      innerHTML: title,
    };
  }

  return {
    attributes: {
      "class": "internal-link",
      "target": "",
      "data-note-icon": noteIcon,
      "href": `${permalink}${headerLinkPath}`,
    },
    innerHTML: title,
  };
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
      md.renderer.rules.hashtag_open = function (tokens, idx) {
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
      openMarker: "```",
      closeMarker: "```",
    })
    .use(namedHeadingsFilter)
    .use(function (md) { /* Custom renderer code omitted */ })
    .use(userMarkdownSetup);

  eleventyConfig.setLibrary("md", markdownLib);

  eleventyConfig.addFilter("isoDate", date => date && date.toISOString());
  eleventyConfig.addFilter("link", function (str) {
    return str?.replace(/\[\[(.*?\|.*?)\]\]/g, function (match, p1) {
      if (p1.indexOf("],[") > -1 || p1.indexOf('"$"') > -1) return match;
      const [fileLink, linkTitle] = p1.split("|");
      return getAnchorLink(fileLink, linkTitle);
    });
  });

  eleventyConfig.addFilter("taggify", str => {
    return str?.replace(tagRegex, (match, precede, tag) => {
      return `${precede}<a class="tag" onclick="toggleTagSearch(this)" data-content="${tag}">${tag}</a>`;
    });
  });

  eleventyConfig.addFilter("searchableTags", str => {
    let tags;
    const match = str?.match(tagRegex);
    if (match) {
      tags = match.map(m => `"${m.split("#")[1]}"`).join(", ");
    }
    return tags ? `${tags},` : "";
  });

  eleventyConfig.addFilter("hideDataview", str =>
    str?.replace(/\(\S+\:\:(.*)\)/g, (_, value) => value.trim())
  );

  eleventyConfig.addTransform("dataview-js-links", str => {
    const parsed = parse(str);
    for (const link of parsed.querySelectorAll("a[data-href].internal-link")) {
      const notePath = link.getAttribute("data-href");
      const title = link.innerHTML;
      const { attributes, innerHTML } = getAnchorAttributes(notePath, title);
      for (const key in attributes) link.setAttribute(key, attributes[key]);
      link.innerHTML = innerHTML;
    }
    return str && parsed.innerHTML;
  });

  eleventyConfig.addTransform("callout-block", str => {
    const parsed = parse(str);
    const transformBlocks = (blocks = parsed.querySelectorAll("blockquote")) => {
      for (const bq of blocks) {
        transformBlocks(bq.querySelectorAll("blockquote"));
        let content = bq.innerHTML;
        let titleDiv = "";
        let calloutType = "";
        let calloutMetaData = "";
        let isCollapsable;
        let isCollapsed;
        const calloutMeta = /\[!([\w-]*)\|?(\s?.*)\](\+|\-){0,1}(\s?.*)/;
        if (!content.match(calloutMeta)) continue;
        content = content.replace(calloutMeta, (match, callout, metaData, collapse, title) => {
          isCollapsable = Boolean(collapse);
          isCollapsed = collapse === "-";
          const titleText = title.replace(/(<\/{0,1}\w+>)/, "")
            ? title
            : `${callout.charAt(0).toUpperCase()}${callout.substring(1).toLowerCase()}`;
          const fold = isCollapsable
            ? `<div class="callout-fold"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="svg-icon lucide-chevron-down"><polyline points="6 9 12 15 18 9"></polyline></svg></div>`
            : "";
          titleDiv = `<div class="callout-title"><div class="callout-title-inner">${titleText}</div>${fold}</div>`;
          return "";
        });
        let contentDiv = content ? `<div class="callout-content">${content}</div>` : "";
        bq.tagName = "div";
        bq.classList.add("callout");
        bq.classList.add(isCollapsable ? "is-collapsible" : "");
        bq.classList.add(isCollapsed ? "is-collapsed" : "");
        bq.setAttribute("data-callout", calloutType.toLowerCase());
        calloutMetaData && bq.setAttribute("data-callout-metadata", calloutMetaData);
        bq.innerHTML = `${titleDiv}${contentDiv}`;
      }
    };
    transformBlocks();
    return str && parsed.innerHTML;
  });

  function fillPictureSourceSets(src, cls, alt, meta, width, imageTag) {
    imageTag.tagName = "picture";
    let html = `<source media="(max-width:480px)" srcset="${meta.webp[0].url}" type="image/webp"/><source media="(max-width:480px)" srcset="${meta.jpeg.url}"/>`;
    if (meta.webp?.[8]?.url) html += `<source media="(max-width:1920px)" srcset="${meta.webp[8].url}" type="image/webp"/>`;
    if (meta.jpeg?.[8]?.url) html += `<source media="(max-width:1920px)" srcset="${meta.jpeg[8].url}"/>`;
    html += `<img class="${cls}" src="${src}" alt="${alt}" width="${width}"/>`;
    imageTag.innerHTML = html;
  }

  eleventyConfig.addTransform("picture", str => {
    if (process.env.USE_FULL_RESOLUTION_IMAGES === "true") return str;
    const parsed = parse(str);
    for (const imageTag of parsed.querySelectorAll(".cm-s-obsidian img")) {
      const src = imageTag.getAttribute("src");
      if (src?.startsWith("/") && !src.endsWith(".svg")) {
        const cls = imageTag.classList.value;
        const alt = imageTag.getAttribute("alt");
        const width = imageTag.getAttribute("width") || "";
        try {
          const meta = transformImage(
            "./src/site" + decodeURI(src),
            cls,
            alt,
            ["(max-width: 480px)", "(max-width: 1024px)"]
          );
          if (meta) fillPictureSourceSets(src, cls, alt, meta, width, imageTag);
        } catch {}
      }
    }
    return str && parsed.innerHTML;
  });

  eleventyConfig.addTransform("table", str => {
    const parsed = parse(str);
    for (const t of parsed.querySelectorAll(".cm-s-obsidian > table")) {
      let inner = t.innerHTML;
      t.tagName = "div";
      t.classList.add("table-wrapper");
      t.innerHTML = `<table>${inner}</table>`;
    }
    for (const t of parsed.querySelectorAll(".cm-s-obsidian > .block-language-dataview > table")) {
      t.classList.add("dataview", "table-view-table");
      t.querySelector("thead")?.classList.add("table-view-thead");
      t.querySelector("tbody")?.classList.add("table-view-tbody");
      t.querySelectorAll("thead > tr")?.forEach(tr => tr.classList.add("table-view-tr-header"));
      t.querySelectorAll("thead > tr > th")?.forEach(th => th.classList.add("table-view-th"));
    }
    return str && parsed.innerHTML;
  });

  eleventyConfig.addTransform("htmlMinifier", (content, outputPath) => {
    if (
      (process.env.NODE_ENV === "production" || process.env.ELEVENTY_ENV === "prod") &&
      outputPath?.endsWith(".html")
    ) {
      return htmlMinifier.minify(content, {
        useShortDoctype: true,
        removeComments: true,
        collapseWhitespace: true,
        conservativeCollapse: true,
        preserveLineBreaks: true,
        minifyCSS: true,
        minifyJS: true,
        keepClosingSlash: true,
      });
    }
    return content;
  });

  eleventyConfig.addPassthroughCopy("src/site/img");
  eleventyConfig.addPassthroughCopy("src/site/scripts");
  eleventyConfig.addPassthroughCopy("src/site/styles/_theme.*.css");
  eleventyConfig.addPlugin(faviconsPlugin, { outputDir: "dist" });
  eleventyConfig.addPlugin(tocPlugin, { ul: true, tags: ["h1","h2","h3","h4","h5","h6"] });
  eleventyConfig.addPlugin(pluginRss, { posthtmlRenderOptions: { closingSingleTag: "slash", singleTags: ["link"] } });

  userEleventySetup(eleventyConfig);

  // Wichtige Änderung: Frontmatter hat immer Vorrang
  eleventyConfig.addGlobalData("eleventyComputed", {
    permalink: data => {
      if (data.permalink) return data.permalink;
      if (data.page.inputPath.toLowerCase().endsWith("/home.md")) return "/index.html";
      return data.page.filePathStem + ".html";
    }
  });

  return {
    dir: { input: "src/site", output: "dist", data: `_data` },
    templateFormats: ["njk","md","11ty.js"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: false,
    passthroughFileCopy: true,
  };
};
