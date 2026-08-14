import { describe, expect, it, vi } from "vitest";
import { classifyLink, routeLinkClick } from "./linkRouting.js";

describe("classifyLink", () => {
  it("leaves anchors in the current document", () => {
    expect(classifyLink("#install")).toEqual({ kind: "anchor" });
  });

  it("routes web URLs to the browser", () => {
    expect(classifyLink("https://example.com/a")).toEqual({ kind: "browser", href: "https://example.com/a" });
  });

  it("routes Markdown paths to a new tab", () => {
    expect(classifyLink("parts/setup.md#install")).toEqual({ kind: "markdown", href: "parts/setup.md#install" });
  });

  it("routes other local paths to the system handler", () => {
    expect(classifyLink("assets/diagram.png")).toEqual({ kind: "file", href: "assets/diagram.png" });
  });

  it("recognizes percent-encoded Windows Markdown paths", () => {
    expect(classifyLink("C:%5Csrc%5Cdist%5CFlatnotes%5Cworkspace%5Cpokeno_readme.md")).toEqual({
      kind: "markdown",
      href: "C:\\src\\dist\\Flatnotes\\workspace\\pokeno_readme.md",
    });
  });

  it("prevents navigation only for non-anchor routes", () => {
    const preventDefault = vi.fn();
    const anchor = { getAttribute: () => "parts/setup.md" };
    const event = { target: { closest: () => anchor }, preventDefault };
    const routed = [];

    expect(routeLinkClick(event, "C:/Notes/guide.md", (route) => routed.push(route))).toBe(true);
    expect(preventDefault).toHaveBeenCalledOnce();
    expect(routed[0]).toEqual({ kind: "markdown", href: "parts/setup.md", path: "C:/Notes/guide.md" });
  });
});
