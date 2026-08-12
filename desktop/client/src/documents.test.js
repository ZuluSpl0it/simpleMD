import { describe, expect, it } from "vitest";
import { classifyDocument } from "./documents.js";

describe("classifyDocument", () => {
  it("marks a selected file inside the workspace as a workspace note", () => {
    const document = classifyDocument(
      { kind: "external", path: "C:\\Notes\\guides\\startup.md", content: "text" },
      "c:/notes",
    );

    expect(document).toMatchObject({ kind: "workspace", title: "guides/startup" });
  });

  it("keeps a file in a similarly named folder external", () => {
    const document = classifyDocument(
      { kind: "external", path: "C:\\Notes-old\\startup.md", content: "text" },
      "C:\\Notes",
    );

    expect(document.kind).toBe("external");
  });

  it("keeps external files external without a workspace", () => {
    expect(classifyDocument({ kind: "external", path: "C:\\Other\\note.md" }, null).kind).toBe("external");
  });
});
