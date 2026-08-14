import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const app = readFileSync(fileURLToPath(new URL("./App.vue", import.meta.url)), "utf8");
const editor = readFileSync(fileURLToPath(new URL("./components/MarkdownEditor.vue", import.meta.url)), "utf8");

it("persists a tab's selected editor mode", () => {
  expect(editor).toMatch(/defineEmits\(\[[^\]]*"mode-change"/);
  expect(editor).toMatch(/changeMode[\s\S]*emit\("mode-change",\s*mode\)/);
  expect(app).toMatch(/@mode-change="\(mode\)\s*=>\s*tabs\.active\.value\.mode\s*=\s*mode"/);
});

it("does not remount the editor while switching Markdown and WYSIWYG", () => {
  expect(app).not.toMatch(/:key="[^"]*tabs\.active\.value\.mode/);
  expect(app).toMatch(/:key="[^"]*tabs\.active\.value\.editing/);
});
