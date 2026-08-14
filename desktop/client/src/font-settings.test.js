import { describe, expect, it, vi } from "vitest";
import { applyFontSettings, DEFAULT_FONT_SIZES } from "./fontSettings.js";

function fakeRoot() {
  const values = {};
  return {
    values,
    style: {
      setProperty: vi.fn((name, value) => { values[name] = value; }),
    },
  };
}

describe("font settings", () => {
  it("applies text, code, and each heading multiplier", () => {
    const root = fakeRoot();
    applyFontSettings(root, {
      text: 16,
      code: 11,
      heading_multiplier: { h1: 2.5 },
    });

    expect(root.values["--flatnotes-text-font-size"]).toBe("16px");
    expect(root.values["--flatnotes-code-font-size"]).toBe("11px");
    expect(root.values["--flatnotes-h1-multiplier"]).toBe("2.5");
    expect(root.values["--flatnotes-h6-multiplier"]).toBe(
      String(DEFAULT_FONT_SIZES.heading_multiplier.h6),
    );
  });

  it("falls back for each malformed browser payload entry", () => {
    const root = fakeRoot();
    applyFontSettings(root, { text: 0, heading_multiplier: { h2: "large" } });

    expect(root.values["--flatnotes-text-font-size"]).toBe(
      `${DEFAULT_FONT_SIZES.text}px`,
    );
    expect(root.values["--flatnotes-code-font-size"]).toBe(
      `${DEFAULT_FONT_SIZES.code}px`,
    );
    expect(root.values["--flatnotes-h2-multiplier"]).toBe(
      String(DEFAULT_FONT_SIZES.heading_multiplier.h2),
    );
  });
});
