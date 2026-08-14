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

  it("routes a rendered-link click when the event target has no closest method", () => {
    const preventDefault = vi.fn();
    const anchor = { tagName: "A", getAttribute: () => "C:%5CNotes%5Cnext.md" };
    const event = {
      target: {},
      composedPath: () => [{}, anchor],
      preventDefault,
    };
    const routed = [];

    expect(routeLinkClick(event, "C:/Notes/current.md", (route) => routed.push(route))).toBe(true);
    expect(preventDefault).toHaveBeenCalledOnce();
    expect(routed[0]).toEqual({
      kind: "markdown",
      href: "C:\\Notes\\next.md",
      path: "C:/Notes/current.md",
    });
  });

  it("routes a destination preserved after the HTML sanitizer removes href", () => {
    const anchor = {
      tagName: "A",
      getAttribute: (name) => name === "data-flatnotes-href" ? "C:%5CNotes%5Cnext.md" : null,
    };
    const event = {
      target: { closest: () => null },
      composedPath: () => [anchor],
      preventDefault: vi.fn(),
    };
    const routed = [];

    expect(routeLinkClick(event, "C:/Notes/current.md", (route) => routed.push(route))).toBe(true);
    expect(routed[0]).toMatchObject({ kind: "markdown", href: "C:\\Notes\\next.md" });
  });

  it("provides a sanitizer-safe attribute for the original destination", async () => {
    const routing = await import("./linkRouting.js");

    expect(routing.linkDestinationAttributes).toBeTypeOf("function");
    expect(routing.linkDestinationAttributes("C:%5CNotes%5Cnext.md")).toEqual({
      "data-flatnotes-href": "C:%5CNotes%5Cnext.md",
    });
  });
});
