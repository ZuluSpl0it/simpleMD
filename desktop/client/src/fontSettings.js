const levels = ["h1", "h2", "h3", "h4", "h5", "h6"];

export const DEFAULT_FONT_SIZES = Object.freeze({
  text: 14,
  code: 12,
  heading_multiplier: Object.freeze({
    h1: 2.4,
    h2: 2.08,
    h3: 1.78,
    h4: 1.5,
    h5: 1.29,
    h6: 1.15,
  }),
});

function pixels(value, fallback) {
  return Number.isInteger(value) && value >= 8 && value <= 72 ? value : fallback;
}

function multiplier(value, fallback) {
  return typeof value === "number"
    && Number.isFinite(value)
    && value >= 0.5
    && value <= 4
    ? value
    : fallback;
}

export function applyFontSettings(root, settings) {
  root.style.setProperty(
    "--flatnotes-text-font-size",
    `${pixels(settings?.text, DEFAULT_FONT_SIZES.text)}px`,
  );
  root.style.setProperty(
    "--flatnotes-code-font-size",
    `${pixels(settings?.code, DEFAULT_FONT_SIZES.code)}px`,
  );
  for (const level of levels) {
    root.style.setProperty(
      `--flatnotes-${level}-multiplier`,
      String(
        multiplier(
          settings?.heading_multiplier?.[level],
          DEFAULT_FONT_SIZES.heading_multiplier[level],
        ),
      ),
    );
  }
}
