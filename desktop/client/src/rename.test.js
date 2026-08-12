import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

const appPath = fileURLToPath(new URL("./App.vue", import.meta.url));

it("guards the file poller while a workspace note is being renamed", () => {
  const source = readFileSync(appPath, "utf8");

  expect(source).toMatch(/tab\.renaming\) return/);
  expect(source).toMatch(/tab\.renaming = true/);
  expect(source).toMatch(/tab\.renaming \|\| tab\.path !== pathBeingChecked/);
});
