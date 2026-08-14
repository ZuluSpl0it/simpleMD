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

  it("returns to Home without closing open tabs", () => {
    const tabs = createTabs();
    const id = tabs.open({ content: "one" });

    tabs.showHome();

    expect(tabs.active.value).toBeUndefined();
    expect(tabs.byId(id).content).toBe("one");
  });

  it("selects an existing tab without changing its content", () => {
    const tabs = createTabs();
    const first = tabs.open({ title: "first", content: "one" });
    const second = tabs.open({ title: "second", content: "two" });

    tabs.select(first);

    expect(tabs.active.value.id).toBe(first);
    expect(tabs.byId(second).content).toBe("two");
  });

  it("stores each tab's editor scroll position", () => {
    const tabs = createTabs();
    const id = tabs.open({ title: "note", content: "one" });
    const position = { view: "viewing", top: 312, ratio: 0.4 };

    tabs.setScrollPosition(id, position);

    expect(tabs.byId(id).scrollPosition).toEqual(position);
  });

  it("replaces a tab from disk and bumps its editor revision", () => {
    const tabs = createTabs();
    const id = tabs.open({ path: "C:/note.md", content: "old", editing: true });
    tabs.setContent(id, "unsaved");
    const previousRevision = tabs.byId(id).editorRevision;

    tabs.replace(id, { content: "new", modified_ns: "42", content_hash: "hash" });

    expect(tabs.byId(id)).toMatchObject({
      content: "new",
      savedContent: "new",
      dirty: false,
      modified_ns: "42",
      content_hash: "hash",
      externalState: null,
    });
    expect(tabs.byId(id).editorRevision).toBe(previousRevision + 1);
  });
});
