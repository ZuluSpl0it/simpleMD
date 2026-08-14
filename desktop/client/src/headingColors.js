const levels = ["h1", "h2", "h3", "h4", "h5", "h6"];

export const DEFAULT_HEADING_COLORS = Object.freeze({
  dark: Object.freeze({
    h1: "#FCA5A5",
    h2: "#FDBA74",
    h3: "#FDE68A",
    h4: "#86EFAC",
    h5: "#93C5FD",
    h6: "#C4B5FD",
  }),
  light: Object.freeze({
    h1: "#B91C1C",
    h2: "#C2410C",
    h3: "#A16207",
    h4: "#15803D",
    h5: "#1D4ED8",
    h6: "#6D28D9",
  }),
});

function validColor(value) {
  return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value);
}

export function applyHeadingColors(root, colors, theme) {
  const activeTheme = theme === "light" ? "light" : "dark";
  const defaults = DEFAULT_HEADING_COLORS[activeTheme];
  const palette = colors?.[activeTheme];
  for (const level of levels) {
    const candidate = palette?.[level];
    root.style.setProperty(
      `--flatnotes-${level}-color`,
      validColor(candidate) ? candidate : defaults[level],
    );
  }
}
