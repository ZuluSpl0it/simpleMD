import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it, vi } from "vitest";
import {
  applyHeadingColors,
  DEFAULT_HEADING_COLORS,
} from "./headingColors.js";

function fakeRoot() {
  const values = {};
  return {
    values,
    style: {
      setProperty: vi.fn((name, value) => { values[name] = value; }),
    },
  };
}

describe("heading colors", () => {
  it("applies all six values from the active theme", () => {
    const root = fakeRoot();
    const colors = structuredClone(DEFAULT_HEADING_COLORS);
    colors.light.h1 = "#010203";
    colors.light.h6 = "#A0B0C0";

    applyHeadingColors(root, colors, "light");

    expect(root.values["--flatnotes-h1-color"]).toBe("#010203");
    expect(root.values["--flatnotes-h6-color"]).toBe("#A0B0C0");
    expect(root.style.setProperty).toHaveBeenCalledTimes(6);
  });

  it("uses frontend defaults when the bridge payload is unavailable", () => {
    const root = fakeRoot();

    applyHeadingColors(root, null, "dark");

    expect(root.values["--flatnotes-h1-color"]).toBe(
      DEFAULT_HEADING_COLORS.dark.h1,
    );
    expect(root.values["--flatnotes-h6-color"]).toBe(
      DEFAULT_HEADING_COLORS.dark.h6,
    );
  });

  it("falls back per entry for a malformed frontend payload", () => {
    const root = fakeRoot();

    applyHeadingColors(root, { dark: { h1: "red", h2: "#112233" } }, "dark");

    expect(root.values["--flatnotes-h1-color"]).toBe(
      DEFAULT_HEADING_COLORS.dark.h1,
    );
    expect(root.values["--flatnotes-h2-color"]).toBe("#112233");
  });
});

it("loads palettes at startup and reapplies them on theme changes", () => {
  const app = readFileSync(
    fileURLToPath(new URL("./App.vue", import.meta.url)),
    "utf8",
  );
  const api = readFileSync(
    fileURLToPath(new URL("./api/desktop.js", import.meta.url)),
    "utf8",
  );

  expect(api).toMatch(/getHeadingColors.*get_heading_colors/);
  expect(app).toMatch(/getHeadingColors/);
  expect(app).toMatch(/headingColors\.value\s*=\s*await getHeadingColors\(\)\.catch/);
  expect(app.match(/applyHeadingColors\(/g)).toHaveLength(2);
});
