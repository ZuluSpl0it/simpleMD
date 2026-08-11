import { describe, expect, it } from "vitest";
import { closeActions } from "./CloseDialog.js";

describe("close actions", () => {
  it("offers save, discard, and cancel for a dirty tab", () => {
    expect(closeActions({ dirty: true })).toEqual(["save", "discard", "cancel"]);
  });
});
