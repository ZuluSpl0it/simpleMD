import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const stylePath = fileURLToPath(new URL("./style.css", import.meta.url));

it("forces Toast UI toolbar icons onto the light sprite row", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(
    /:root\[data-theme="light"\]\s+\.toastui-editor-toolbar-icons\s*\{[^}]*background-position-y:\s*3px\s*!important/,
  );
});

it("does not let app button backgrounds erase the Toast UI icon sprite", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/button:not\(\.toastui-editor-toolbar-icons\)\s*\{/);
  expect(css).toMatch(/:root\[data-theme="light"\]\s+button:not\(\.toastui-editor-toolbar-icons\)/);
});

it("uses light surfaces for dialogs and conflict popups", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/:root\[data-theme="light"\]\s+\.conflict,/);
  expect(css).toMatch(/:root\[data-theme="light"\]\s+\.close-dialog\s*\{[^}]*background:\s*#ffffff[^}]*color:\s*#292524/);
  expect(css).toMatch(/:root\[data-theme="light"\]\s+\.modal-backdrop\s*\{[^}]*background:\s*#57534e66/);
});

it("keeps the rebuild-index action visible on the home screen", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/\.home\s+\.rebuild-index-button\s*\{[^}]*display:\s*inline-block/);
});

it("uses larger, more distinct heading sizes in the editor and heading picker", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s*\{[^}]*font-size:\s*var\(--flatnotes-font-size\)/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+p,/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+li\s*\{[^}]*font-size:\s*var\(--flatnotes-font-size\)/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+h1\s*\{[^}]*font-size:\s*calc\(var\(--flatnotes-font-size\) \* 2\)/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+h6\s*\{[^}]*font-size:\s*calc\(var\(--flatnotes-font-size\) \* \.9412\)/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+pre,/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+pre\s+code\s*\{[^}]*font-size:\s*var\(--flatnotes-code-font-size\)/);
  expect(css).toMatch(/\.toastui-editor-popup-add-heading\s+h1\s*\{[^}]*font-size:\s*30px/);
  expect(css).toMatch(/\.toastui-editor-popup-add-heading\s+h6\s*\{[^}]*font-size:\s*16px/);
});

it("uses configurable typography variables in reading and editing views", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/--flatnotes-font-size:\s*17px/);
  expect(css).toMatch(/--flatnotes-code-font-size:\s*13px/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+p,[\s\S]*font-size:\s*var\(--flatnotes-font-size\)/);
  expect(css).toMatch(/\.editor-shell\.editing\s+\.editor\.markdown-only[\s\S]*font-size:\s*var\(--flatnotes-font-size\)/);
  expect(css).toMatch(/\.editor-shell\.editing\s+\.editor\.markdown-only\s+\.ProseMirror\s*\{[^}]*font-size:\s*var\(--flatnotes-font-size\)\s*!important/);
  expect(css).toMatch(/\.editor-shell\.editing\s+\.editor\.markdown-only\s+\.ProseMirror\s+\.toastui-editor-md-heading1\s*\{[^}]*font-size:\s*calc\(var\(--flatnotes-font-size\) \* 2\)/);
  expect(css).toMatch(/\.editor-shell\.editing[\s\S]*\.toastui-editor-contents\s+pre\s+code[\s\S]*font-size:\s*var\(--flatnotes-code-font-size\)/);
});

it("flattens only WYSIWYG paragraphs created by soft breaks", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/\.editor-shell\.editing\s+\.editor\s+\.toastui-editor-ww-container/);
  expect(css).not.toMatch(/\.editor-shell\.editing\s+\.editor:not\(\.markdown-only\)\s+\.toastui-editor-ww-container/);
  expect(css).toMatch(/\.toastui-editor-contents\s*>\s*p\.flatnotes-softbreak[\s,\S]*\{[^}]*display:\s*inline/);
  expect(css).toMatch(/p\.flatnotes-softbreak-before\s*\{[^}]*display:\s*inline/);
});

it("matches WYSIWYG heading line spacing to the reader", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/\.toastui-editor-ww-container\s+\.toastui-editor-contents\s+h1\s*\{[^}]*line-height:\s*1\.2/);
  expect(css).toMatch(/\.toastui-editor-ww-container\s+\.toastui-editor-contents\s+h2\s*\{[^}]*line-height:\s*1\.25/);
  expect(css).toMatch(/\.toastui-editor-ww-container\s+\.toastui-editor-contents\s+h3\s*\{[^}]*line-height:\s*1\.3/);
  expect(css).toMatch(/\.toastui-editor-ww-container\s+\.toastui-editor-contents\s+h4\s*\{[^}]*line-height:\s*1\.35/);
  expect(css).toMatch(/\.toastui-editor-ww-container\s+\.toastui-editor-contents\s+h5\s*\{[^}]*line-height:\s*1\.4/);
  expect(css).toMatch(/\.toastui-editor-ww-container\s+\.toastui-editor-contents\s+h6\s*\{[^}]*line-height:\s*1\.45/);
});
