function normalizePath(path) {
  return String(path || "").replaceAll("\\", "/").replace(/\/+$/, "").toLocaleLowerCase();
}

export function classifyDocument(document, workspace) {
  const path = normalizePath(document?.path);
  const root = normalizePath(workspace);
  if (!path || !root || !(path === root || path.startsWith(`${root}/`))) return document;

  const relative = path.slice(root.length + 1).replace(/\.md$/i, "");
  return { ...document, kind: "workspace", title: relative };
}
