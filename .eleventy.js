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
  return `<a ${Object.keys(attributes)
    .map((key) => `${key}="${attributes[key]}"`)
    .join(" ")}>${innerHTML}</a>`;
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
    if (frontMatter.data.tags && frontMatter.data.tags.includes("gardenEntry")) {
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
        class: "internal-link is-unresolved",
        href: "/404",
        target: "",
      },
      innerHTML: title,
    };
  }
  return {
    attributes: {
      class: "internal-link",
      target: "",
      "data-note-icon": noteIcon,
      href: `${permalink}${headerLinkPath}`,
    },
    innerHTML: title,
  };
}

const tagRegex = /(^|\s|\>)(#[^\s!@#$%^&*()=+\.,\[{\]};:'"?><]+)(?!([^<]*>))/g;

module.exports = function (eleventyConfig) {
  eleventyConfig.setLiquidOptions({ dynamicPartials: true });

  // --- Passthrough Copy ---
  eleventyConfig.addPassthroughCopy("src/site/img/user/z_Images"); 
  eleventyConfig.addPassthroughCopy("src/site/scripts");
  eleventyConfig.addPassthroughCopy("src/site/styles");
  eleventyConfig.addPassthroughCopy("src/site/styles/_theme.*.css");

  // --- Markdown Setup ---
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

  // --- Filters ---
  eleventyConfig.addFilter("isoDate", (date) => date && date.toISOString());
  eleventyConfig.addFilter("link", (str) => {
    return (
      str &&
      str.replace(/\[\[(.*?\|.*?)\]\]/g, (match, p1) => {
        if (p1.includes("],[") || p1.includes('"$"')) return match;
        const [fileLink, linkTitle] = p1.split("|");
        return getAnchorLink(fileLink, linkTitle);
      })
    );
  });
  eleventyConfig.addFilter("taggify", (str) =>
    str?.replace(tagRegex, (match, precede, tag) => {
      return `${precede}<a class="tag" onclick="toggleTagSearch(this)" data-content="${tag}">${tag}</a>`;
    })
  );
  eleventyConfig.addFilter("searchableTags", (str) => {
    const tags = str?.match(tagRegex)?.map((m) => `"${m.split("#")[1]}"`)?.join(", ");
    return tags ? `${tags},` : "";
  });
  eleventyConfig.addFilter("hideDataview", (str) =>
    str?.replace(/\(\S+\:\:(.*)\)/g, (_, value) => value.trim())
  );
  eleventyConfig.addFilter("dateToZulu", (date) => date?.toISOString() || "");
  eleventyConfig.addFilter("jsonify", (v) => JSON.stringify(v) || '""');
  eleventyConfig.addFilter("validJson", (v) => {
    if (Array.isArray(v)) return v.map((x) => x.replaceAll("\\", "\\\\")).join(",");
    if (typeof v === "string") return v.replaceAll("\\", "\\\\");
    return v;
  });

  // --- Transforms ---
  eleventyConfig.addTransform("dataview-js-links", function (str) {
    const parsed = parse(str);
    for (const dataViewJsLink of parsed.querySelectorAll("a[data-href].internal-link")) {
      const notePath = dataViewJsLink.getAttribute("data-href");
      const title = dataViewJsLink.innerHTML;
      const { attributes, innerHTML } = getAnchorAttributes(notePath, title);
      for (const key in attributes) dataViewJsLink.setAttribute(key, attributes[key]);
      dataViewJsLink.innerHTML = innerHTML;
    }
    return parsed?.innerHTML;
  });

  eleventyConfig.addTransform("resolveImageLinks", (content, outputPath) => {
    if (outputPath && outputPath.endsWith(".html")) {
      return content.replace(/!\[\[(.+?)\]\]/g, (match, imgName) => {
        const src = `/choke-slam-wrestling/img/user/z_Images/${imgName}`;
        return `<img src="${src}" alt="${imgName}" loading="lazy">`;
      });
    }
    return content;
  });
  
  // --- Universeller Fix für alle absoluten DG-Links auf GitHub Pages Subfolder ---
  const GHP_SUBFOLDER = "/choke-slam-wrestling";

  eleventyConfig.addTransform("fixDGAbsoluteLinks", (content, outputPath) => {
    if (outputPath && outputPath.endsWith(".html")) {
      // Links, die mit / beginnen, aber nicht extern sind (https://, mailto:, #)
      return content.replace(
        /href="\/(?!\/|http|https|#|mailto)([^"]+)"/g,
        (match, p1) => `href="${GHP_SUBFOLDER}/${p1}"`
      );
    }
    return content;
  });

  // --- Plugins ---
  eleventyConfig.addPlugin(faviconsPlugin, { outputDir: "dist" });
  eleventyConfig.addPlugin(tocPlugin, { ul: true, tags: ["h1", "h2", "h3", "h4", "h5", "h6"] });
  eleventyConfig.addPlugin(pluginRss, {
    posthtmlRenderOptions: { closingSingleTag: "slash", singleTags: ["link"] },
  });

  // --- User custom setup ---
  userEleventySetup(eleventyConfig);

  // --- Eleventy Config Return ---
  return {
    dir: {
      input: "src/site",
      output: "dist",
      data: "_data",
    },
    templateFormats: ["njk", "md", "11ty.js"],
    htmlTemplateEngine: "njk",
    markdownTemplateEngine: false,
    passthroughFileCopy: true,
    pathPrefix: "/choke-slam-wrestling/",
  };
};
