import { describe, expect, it } from "vitest";
import { findMatches } from "./find.js";

describe("findMatches", () => {
  it("finds case-insensitive non-overlapping matches", () => {
    expect(findMatches("Flatnotes notes FLATNOTES", "notes")).toEqual([
      { start: 4, end: 9 },
      { start: 10, end: 15 },
      { start: 20, end: 25 },
    ]);
  });

  it("returns no matches for an empty query", () => {
    expect(findMatches("content", "")).toEqual([]);
  });
});
