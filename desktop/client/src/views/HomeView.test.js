import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const source = readFileSync(
  fileURLToPath(new URL("./HomeView.vue", import.meta.url)),
  "utf8",
);

describe("HomeView search", () => {
  it("blocks submission while the index is busy", () => {
    expect(source).toMatch(/props\.indexBusy\s*\|\|\s*!query/);
  });

  it("opens accessible search help and restores trigger focus", () => {
    expect(source).toMatch(/SearchHelpDialog/);
    expect(source).toMatch(/aria-label="Search help"/);
    expect(source).toMatch(/:aria-expanded="searchHelpOpen"/);
    expect(source).toMatch(/aria-controls="search-help-dialog"/);
    expect(source).toMatch(/data-tooltip="Search help"/);
    expect(source).toMatch(/@close="closeSearchHelp"/);
    expect(source).toMatch(/searchHelpButton\.value\?\.focus\(\)/);
  });

  it("catches search failures and exposes an alert", () => {
    expect(source).toMatch(/try\s*\{/);
    expect(source).toMatch(/catch\s*\(error\)/);
    expect(source).toMatch(/results\.value\s*=\s*\[\]/);
    expect(source).toMatch(/role="alert"/);
  });
});
