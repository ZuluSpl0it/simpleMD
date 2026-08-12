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

  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s*\{[^}]*font-size:\s*16px/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+p,/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+li\s*\{[^}]*font-size:\s*17px/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+h1\s*\{[^}]*font-size:\s*34px/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+h6\s*\{[^}]*font-size:\s*16px/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+pre,/);
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+pre\s+code\s*\{[^}]*font-size:\s*13px/);
  expect(css).toMatch(/\.toastui-editor-popup-add-heading\s+h1\s*\{[^}]*font-size:\s*30px/);
  expect(css).toMatch(/\.toastui-editor-popup-add-heading\s+h6\s*\{[^}]*font-size:\s*16px/);
});
