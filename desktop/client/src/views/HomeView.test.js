import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const viewPath = fileURLToPath(new URL("./HomeView.vue", import.meta.url));

it("uses the HomeView indexBusy prop when submitting search", () => {
  const source = readFileSync(viewPath, "utf8");

  expect(source).toMatch(/if \(!props\.indexBusy && term\.value\.trim\(\)\)/);
});
