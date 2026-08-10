import { describe, expect, it } from "vitest";
import { createTabs } from "./tabs.js";

describe("tabs", () => {
  it("marks an edited tab dirty", () => {
    const tabs = createTabs();
    const id = tabs.open({ path: "C:/outside.md", kind: "external", content: "one" });
    tabs.setContent(id, "two");
    expect(tabs.byId(id).dirty).toBe(true);
  });

  it("requires resolution before closing dirty tab", () => {
    const tabs = createTabs();
    const id = tabs.open({ content: "one" });
    tabs.setContent(id, "two");
    expect(tabs.requestClose(id)).toEqual({ requiresConflict: true });
  });
});
