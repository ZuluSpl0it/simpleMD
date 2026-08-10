import { describe, expect, it } from "vitest";
import { conflictActions } from "./ConflictDialog.js";

describe("conflict actions", () => {
  it("offers all choices for a dirty changed tab", () => {
    expect(conflictActions({ dirty: true, externalState: "changed" })).toEqual([
      "reload",
      "overwrite",
      "saveAs",
    ]);
  });

  it("only offers save-as for missing file", () => {
    expect(conflictActions({ dirty: true, externalState: "missing" })).toEqual([
      "saveAs",
    ]);
  });
});
