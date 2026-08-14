import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const component = readFileSync(
  fileURLToPath(new URL("./TextInputDialog.vue", import.meta.url)),
  "utf8",
);

describe("TextInputDialog", () => {
  it("exposes a themed dialog with submit and cancel actions", () => {
    expect(component).toMatch(/role="dialog"/);
    expect(component).toMatch(/aria-modal="true"/);
    expect(component).toMatch(/@submit\.prevent="submit"/);
    expect(component).toMatch(/type="submit"/);
    expect(component).toMatch(/@click="cancel"/);
    expect(component).toMatch(/@keydown\.escape="cancel"/);
  });

  it("accepts title, label, initial value, and action text", () => {
    expect(component).toMatch(/title:\s*\{/);
    expect(component).toMatch(/label:\s*\{/);
    expect(component).toMatch(/value:\s*\{/);
    expect(component).toMatch(/confirmLabel:\s*\{/);
    expect(component).toMatch(/defineEmits\(\["submit",\s*"cancel"\]/);
  });
});
