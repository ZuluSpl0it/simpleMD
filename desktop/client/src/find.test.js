import { describe, expect, it } from "vitest";
import { findMatches, replaceAllMatches, replaceMatch } from "./find.js";

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

  it("replaces only the active case-insensitive match", () => {
    expect(replaceMatch("One one ONE", "one", "two", 1)).toBe("One two ONE");
  });

  it("replaces every non-overlapping match", () => {
    expect(replaceAllMatches("Flatnotes notes FLATNOTES", "notes", "docs")).toBe("Flatdocs docs FLATdocs");
  });

  it("treats replacement text literally and makes invalid requests no-ops", () => {
    expect(replaceAllMatches("a.b A.B", "a.b", "$& [x]")).toBe("$& [x] $& [x]");
    expect(replaceMatch("content", "", "x", 0)).toBe("content");
    expect(replaceMatch("one", "missing", "x", 0)).toBe("one");
    expect(replaceMatch("one", "one", "x", 4)).toBe("one");
  });
});
