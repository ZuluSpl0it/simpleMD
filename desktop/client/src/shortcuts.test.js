import { describe, expect, it } from "vitest";
import { isShortcut } from "./shortcuts.js";

describe("keyboard shortcuts", () => {
  it("recognizes save and redo shortcuts on Windows and macOS", () => {
    expect(isShortcut({ ctrlKey: true, metaKey: false, code: "KeyS" }, "KeyS")).toBe(true);
    expect(isShortcut({ ctrlKey: false, metaKey: true, code: "KeyS" }, "KeyS")).toBe(true);
    expect(isShortcut({ ctrlKey: true, metaKey: false, code: "KeyY" }, "KeyY")).toBe(true);
  });

  it("does not treat an unmodified key as a shortcut", () => {
    expect(isShortcut({ ctrlKey: false, metaKey: false, code: "KeyS" }, "KeyS")).toBe(false);
    expect(isShortcut({ ctrlKey: true, metaKey: false, code: "KeyS" }, "KeyY")).toBe(false);
  });
});
