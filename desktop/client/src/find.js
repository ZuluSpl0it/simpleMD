export function findMatches(text, query) {
  const needle = query.trim().toLocaleLowerCase();
  if (!needle) return [];

  const haystack = text.toLocaleLowerCase();
  const matches = [];
  let start = 0;
  while (start < haystack.length) {
    const index = haystack.indexOf(needle, start);
    if (index === -1) break;
    matches.push({ start: index, end: index + needle.length });
    start = index + needle.length;
  }
  return matches;
}

export function replaceMatch(text, query, replacement, activeIndex = 0) {
  const matches = findMatches(text, query);
  const match = matches[activeIndex];
  if (!match) return text;
  return text.slice(0, match.start) + replacement + text.slice(match.end);
}

export function replaceAllMatches(text, query, replacement) {
  const matches = findMatches(text, query);
  if (!matches.length) return text;
  let result = text;
  for (let index = matches.length - 1; index >= 0; index -= 1) {
    const match = matches[index];
    result = result.slice(0, match.start) + replacement + result.slice(match.end);
  }
  return result;
}

function clearHighlights() {
  if (!globalThis.CSS?.highlights) return;
  globalThis.CSS.highlights.delete("flatnotes-find");
  globalThis.CSS.highlights.delete("flatnotes-find-current");
}

export function highlightMatches(root, query, activeIndex = 0) {
  clearHighlights();
  if (!root || !query.trim()) return 0;

  const textNodes = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const parent = node.parentElement;
      if (!parent || ["SCRIPT", "STYLE"].includes(parent.tagName)) {
        return NodeFilter.FILTER_REJECT;
      }
      return node.nodeValue ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
    },
  });
  let node;
  while ((node = walker.nextNode())) textNodes.push(node);

  const matches = [];
  const needle = query.trim().toLocaleLowerCase();
  for (const textNode of textNodes) {
    const text = textNode.nodeValue;
    const lower = text.toLocaleLowerCase();
    let start = 0;
    while (start < lower.length) {
      const index = lower.indexOf(needle, start);
      if (index === -1) break;
      const range = new Range();
      range.setStart(textNode, index);
      range.setEnd(textNode, index + needle.length);
      matches.push(range);
      start = index + needle.length;
    }
  }

  if (!globalThis.Highlight || !globalThis.CSS?.highlights) return matches.length;

  const current = matches[activeIndex];
  const all = new Highlight(...matches);
  globalThis.CSS.highlights.set("flatnotes-find", all);
  if (current) globalThis.CSS.highlights.set("flatnotes-find-current", new Highlight(current));
  current?.startContainer.parentElement?.scrollIntoView({ block: "nearest" });
  return matches.length;
}

export function clearFindHighlights() {
  clearHighlights();
}
