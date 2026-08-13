import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const appPath = fileURLToPath(new URL("./App.vue", import.meta.url));

it("handles a drop payload containing multiple paths independently", () => {
  const source = readFileSync(appPath, "utf8");

  expect(source).toMatch(/event\.detail\?\.paths/);
  expect(source).toMatch(/for \(const path of paths\)/);
  expect(source).toMatch(/await openDroppedPath\(path\)/);
  expect(source).toMatch(/tabs\.open\(classifyDocument\(document, workspace\.value\)\)/);
  expect(source).toMatch(/catch \(_error\)/);
});

it("keeps the existing single-document drop payload compatible", () => {
  const source = readFileSync(appPath, "utf8");

  expect(source).toMatch(/event\.detail\?\.path/);
  expect(source).toMatch(/event\.detail\?\.kind/);
});
