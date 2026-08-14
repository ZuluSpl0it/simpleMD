import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const app = readFileSync(fileURLToPath(new URL("./App.vue", import.meta.url)), "utf8");

it("uses the themed input dialog for save and rename", () => {
  expect(app).toMatch(/TextInputDialog/);
  expect(app).toMatch(/@submit="resolveInputDialog"/);
  expect(app).toMatch(/@cancel="cancelInputDialog"/);
  expect(app).toMatch(/inputDialog/);
  expect(app).not.toMatch(/window\.prompt\(/);
});
