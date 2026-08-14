export function classifyLink(href) {
  const value = String(href || "");
  if (!value || value.startsWith("#")) return { kind: "anchor" };
  const parsed = new URL(value, "file:///flatnotes/current.md");
  if (parsed.protocol === "http:" || parsed.protocol === "https:") return { kind: "browser", href: value };
  if (parsed.protocol === "file:" && parsed.pathname.toLowerCase().endsWith(".md")) return { kind: "markdown", href: value };
  if (parsed.protocol === "file:") return { kind: "file", href: value };
  return { kind: "file", href: value };
}

export function routeLinkClick(event, currentPath, onRoute) {
  const anchor = event.target?.closest?.("a[href]");
  if (!anchor) return false;
  const route = classifyLink(anchor.getAttribute("href"));
  if (route.kind === "anchor") return false;
  event.preventDefault();
  onRoute({ ...route, path: currentPath });
  return true;
}
