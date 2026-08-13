import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const viewPath = fileURLToPath(new URL("./FindBar.vue", import.meta.url));

it("keeps replacement controls inside edit mode", () => {
  const source = readFileSync(viewPath, "utf8");

  expect(source).toMatch(/editing/);
  expect(source).toMatch(/v-if="editing"/);
  expect(source).toMatch(/Replace/);
  expect(source).toMatch(/Replace All/);
  expect(source).toMatch(/update:replacement/);
  expect(source).toMatch(/replace-all/);
});
