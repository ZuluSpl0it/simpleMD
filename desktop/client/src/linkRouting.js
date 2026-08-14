export function classifyLink(href) {
  const value = String(href || "");
  if (!value || value.startsWith("#")) return { kind: "anchor" };
  let decoded = value;
  try {
    decoded = decodeURIComponent(value);
  } catch (_error) {
    // Preserve malformed URLs for the bridge to report.
  }
  if (/^[A-Za-z]:[\\/]/.test(decoded) || decoded.startsWith("\\\\")) {
    const path = decoded.split("#", 1)[0];
    return { kind: path.toLowerCase().endsWith(".md") ? "markdown" : "file", href: decoded };
  }
  const parsed = new URL(value, "file:///flatnotes/current.md");
  if (parsed.protocol === "http:" || parsed.protocol === "https:") return { kind: "browser", href: value };
  if (parsed.protocol === "file:" && parsed.pathname.toLowerCase().endsWith(".md")) return { kind: "markdown", href: value };
  if (parsed.protocol === "file:") return { kind: "file", href: value };
  return { kind: "file", href: value };
}

export function linkDestinationAttributes(destination) {
  return { "data-flatnotes-href": String(destination || "") };
}

function linkAnchorFromEvent(event) {
  const closest = event.target?.closest?.("a[href], a[data-flatnotes-href]");
  if (closest) return closest;
  return event.composedPath?.().find((node) => (
    node?.tagName === "A"
    && (node.getAttribute?.("data-flatnotes-href") || node.getAttribute?.("href"))
  )) || null;
}

export function routeLinkClick(event, currentPath, onRoute) {
  const anchor = linkAnchorFromEvent(event);
  if (!anchor) return false;
  const route = classifyLink(anchor.getAttribute("data-flatnotes-href") || anchor.getAttribute("href"));
  if (route.kind === "anchor") return false;
  event.preventDefault();
  onRoute({ ...route, path: currentPath });
  return true;
}
