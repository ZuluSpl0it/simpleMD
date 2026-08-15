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

it("keeps search help controls stable and themed", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/\.search-help-button\s*\{[^}]*width:\s*40px[^}]*border-radius:\s*0/);
  expect(css).toMatch(/\.search-help-button::after\s*\{[^}]*content:\s*attr\(data-tooltip\)/);
  expect(css).toMatch(/\.search-help-button:hover::after,[\s\S]*\.search-help-button:focus-visible::after/);
  expect(css).toMatch(/\.home\s+\.search-error\s*\{[^}]*color:\s*#f87171/);
  expect(css).toMatch(/:root\[data-theme="light"\]\s+\.search-help-dialog\s*\{[^}]*background:\s*#ffffff[^}]*color:\s*#292524/);
});

it("uses configurable text, code, and heading multipliers", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(/--flatnotes-text-font-size:\s*14px/);
  expect(css).toMatch(/--flatnotes-code-font-size:\s*12px/);
  for (const level of ["h1", "h2", "h3", "h4", "h5", "h6"]) {
    const number = level.slice(1);
    expect(css).toMatch(new RegExp(`--flatnotes-${level}-multiplier:`));
    expect(css).toMatch(new RegExp(
      `\.editor\.viewing\\s+\.toastui-editor-contents\\s+${level}\\s*\\{[^}]*font-size:\\s*calc\\(\\s*var\\(--flatnotes-text-font-size\\) \\* var\\(--flatnotes-${level}-multiplier\\)`,
    ));
    expect(css).toMatch(new RegExp(
      `\.toastui-editor-md-heading${number}\\s*\\{[^}]*font-size:\\s*calc\\(\\s*var\\(--flatnotes-text-font-size\\) \\* var\\(--flatnotes-${level}-multiplier\\)`,
    ));
    expect(css).toMatch(new RegExp(
      `\.toastui-editor-ww-container\\s+\.toastui-editor-contents\\s+${level}\\s*\\{[^}]*font-size:\\s*calc\\(\\s*var\\(--flatnotes-text-font-size\\) \\* var\\(--flatnotes-${level}-multiplier\\)`,
    ));
  }
  expect(css).toMatch(/\.editor\.viewing\s+\.toastui-editor-contents\s+p,[\s\S]*font-size:\s*var\(--flatnotes-text-font-size\)/);
  expect(css).toMatch(/\.editor-shell\.editing\s+\.editor\.markdown-only[\s\S]*font-size:\s*var\(--flatnotes-text-font-size\)/);
  expect(css).toMatch(/\.toastui-editor-contents\s+pre\s+code[\s\S]*font-size:\s*var\(--flatnotes-code-font-size\)/);
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

it("colors headings only in reader and WYSIWYG views", () => {
  const css = readFileSync(stylePath, "utf8");

  for (let level = 1; level <= 6; level += 1) {
    expect(css).toMatch(new RegExp(
      `\\.editor\\.viewing\\s+\\.toastui-editor-contents\\s+h${level}\\s*\\{[^}]*color:\\s*var\\(--flatnotes-h${level}-color\\)`,
    ));
    expect(css).toMatch(new RegExp(
      `\\.toastui-editor-ww-container\\s+\\.toastui-editor-contents\\s+h${level}\\s*\\{[^}]*color:\\s*var\\(--flatnotes-h${level}-color\\)`,
    ));
  }

  expect(css).not.toMatch(/markdown-only[^}]*--flatnotes-h[1-6]-color/);
  expect(css).not.toMatch(/border[^;}]*var\(--flatnotes-h[1-6]-color\)/);
});

it("uses a darker code-block surface in rendered light-theme views", () => {
  const css = readFileSync(stylePath, "utf8");

  expect(css).toMatch(
    /:root\[data-theme="light"\]\s+\.toastui-editor-contents\s+pre\s*\{[^}]*background:\s*#e7e5e4/,
  );
});
