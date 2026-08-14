import { expect, it, vi } from "vitest";
import { configureWysiwygSoftBreaks } from "./softBreaks.js";

it("marks the paragraph opened for a soft break", () => {
  const original = vi.fn();
  const editor = { convertor: { toWwConvertors: { softbreak: original } } };
  const closeNode = vi.fn();
  const openNode = vi.fn();
  const current = { type: { name: "paragraph" }, attrs: null };
  const state = {
    schema: { nodes: { paragraph: "paragraph" } },
    top: () => current,
    closeNode,
    openNode,
  };

  expect(configureWysiwygSoftBreaks(editor)).toBe(true);
  editor.convertor.toWwConvertors.softbreak(state, {
    parent: { type: "paragraph" },
    prev: { type: "text" },
    next: { type: "text" },
  });

  expect(original).not.toHaveBeenCalled();
  expect(current.attrs.classNames).toEqual(["flatnotes-softbreak-before"]);
  expect(closeNode).toHaveBeenCalledOnce();
  expect(openNode).toHaveBeenCalledWith("paragraph", {
    classNames: ["flatnotes-softbreak"],
  });
});
