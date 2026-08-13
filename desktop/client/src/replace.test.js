import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const appPath = fileURLToPath(new URL("./App.vue", import.meta.url));

it("wires edit-only find and replace actions through the active tab", () => {
  const source = readFileSync(appPath, "utf8");

  expect(source).toMatch(/replaceMatch/);
  expect(source).toMatch(/replaceAllMatches/);
  expect(source).toMatch(/:editing="tabs\.active\.value\.editing"/);
  expect(source).toMatch(/:replacement="replacementQuery"/);
  expect(source).toMatch(/@replace="replaceActive"/);
  expect(source).toMatch(/@replace-all="replaceAllActive"/);
  expect(source).toMatch(/tabs\.setContent/);
});
