import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const appPath = fileURLToPath(new URL("./App.vue", import.meta.url));

it("loads persisted font settings before opening the workspace", () => {
  const source = readFileSync(appPath, "utf8");

  expect(source).toMatch(/getFontSettings/);
  expect(source).toMatch(/getFontSettings\(\)/);
  expect(source).toMatch(/getFontSettings\(\)\.catch/);
  expect(source).toMatch(/--flatnotes-font-size/);
  expect(source).toMatch(/--flatnotes-code-font-size/);
});
