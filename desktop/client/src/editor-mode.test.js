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

it("disables save actions until the active tab is dirty", () => {
  const tabBar = readFileSync(fileURLToPath(new URL("./components/TabBar.vue", import.meta.url)), "utf8");
  expect(tabBar).toMatch(/:disabled=\"!active\.dirty\"\s+@click=\"\$emit\('save'\)\"/);
  expect(tabBar).toMatch(/:disabled=\"!active\.dirty\"\s+@click=\"\$emit\('save-as'\)\"/);
});

it("adds a toolbar command for inserting a hard HTML break", () => {
  expect(editor).toMatch(/name:\s*"lineBreak"/);
  expect(editor).toMatch(/className:\s*"line-break toastui-editor-toolbar-icons"/);
  expect(editor).toMatch(/tooltip:\s*"Line Break"/);
  expect(editor).toMatch(/command:\s*"insertLineBreak"/);
  expect(editor).toMatch(/addCommand\("markdown",\s*"insertLineBreak"/);
  expect(editor).toMatch(/insertText\("<br>"\)/);
  expect(editor).toMatch(/addCommand\("wysiwyg",\s*"insertLineBreak"/);
  expect(editor).toMatch(/insertWysiwygLineBreak/);
});

it("preserves HTML breaks through WYSIWYG mode changes", () => {
  expect(editor).toMatch(/widgetRules:\s*\[/);
  expect(editor).toMatch(/rule:\s*new RegExp\(lineBreakMarker\)/);
  expect(editor).toMatch(/handleModeSwitchClick[\s\S]*markdownForWysiwyg/);
  expect(editor).toMatch(/addEventListener\("click",\s*handleModeSwitchClick,\s*true\)/);
  expect(editor).toMatch(/decodeEditorLineBreaks\(editor\.getMarkdown\(\)\)/);
  expect(editor).not.toMatch(/htmlInline:\s*\{\s*br:/);
  expect(editor).not.toMatch(/rule:\s*\/<br/);
});
