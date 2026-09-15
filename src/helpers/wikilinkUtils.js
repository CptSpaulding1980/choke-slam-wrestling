function splitWikiLink(value) {
  const separator = value.indexOf('|');
  if (separator === -1) {
    return [value.replace(/\\$/, ''), undefined];
  }
  const target = value.slice(0, separator).replace(/\\$/, '');
  return [target, value.slice(separator + 1)];
}

module.exports = { splitWikiLink };
