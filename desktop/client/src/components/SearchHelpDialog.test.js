import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const component = readFileSync(
  fileURLToPath(new URL("./SearchHelpDialog.vue", import.meta.url)),
  "utf8",
);

describe("SearchHelpDialog", () => {
  it("exposes an accessible modal with every close path", () => {
    expect(component).toMatch(/id="search-help-dialog"/);
    expect(component).toMatch(/role="dialog"/);
    expect(component).toMatch(/aria-modal="true"/);
    expect(component).toMatch(/aria-labelledby="search-help-title"/);
    expect(component).toMatch(/@click\.self="close"/);
    expect(component).toMatch(/@keydown\.escape\.stop\.prevent="close"/);
    expect(component).toMatch(/aria-label="Close search help"/);
    expect(component).toMatch(/closeButton\.value\?\.focus\(\)/);
  });

  it("documents the supported query formats", () => {
    for (const example of [
      "terra validator",
      "&quot;bonding curve&quot;",
      "terra*",
      "te?t",
      "terrd~",
      "terrad~2",
      "title:curve",
      "tags:terra",
      "terra AND validator",
    ]) {
      expect(component).toContain(example);
    }
  });
});
