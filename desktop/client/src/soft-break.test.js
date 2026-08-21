import { expect, it, vi } from "vitest";
import {
  configureWysiwygSoftBreaks,
  decodeEditorLineBreaks,
  encodeHtmlLineBreaks,
  insertWysiwygLineBreak,
  lineBreakMarker,
  markdownForWysiwyg,
} from "./softBreaks.js";

function rootWith(...nodes) {
  return {
    walker() {
      let index = 0;
      return { next: () => (index < nodes.length ? { entering: true, node: nodes[index++] } : null) };
    },
  };
}

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

it("leaves the HTML converter untouched", () => {
  const originalHtmlInline = vi.fn();
  const editor = {
    convertor: {
      toWwConvertors: {
        softbreak: vi.fn(),
        htmlInline: originalHtmlInline,
      },
    },
  };
  configureWysiwygSoftBreaks(editor);
  expect(editor.convertor.toWwConvertors.htmlInline).toBe(originalHtmlInline);
});

it("encodes semantic HTML breaks without changing code literals", () => {
  const markdown = "alpha<br>beta and `<br>`";
  const root = rootWith(
    { type: "htmlInline", literal: "<br>", sourcepos: [[1, 6], [1, 9]] },
    { type: "code", literal: "<br>", sourcepos: [[1, 19], [1, 24]] },
  );

  expect(encodeHtmlLineBreaks(markdown, root)).toBe(`alpha${lineBreakMarker}beta and \`<br>\``);
});

it("decodes consecutive widget wrappers to literal HTML breaks", () => {
  const markdown = `alpha$$widget0 ${lineBreakMarker}$$$$widget0 ${lineBreakMarker}$$beta`;
  expect(decodeEditorLineBreaks(markdown)).toBe("alpha<br><br>beta");
});

it("parses external Markdown before encoding WYSIWYG breaks", () => {
  const root = rootWith({ type: "htmlInline", literal: "<br>", sourcepos: [[1, 6], [1, 9]] });
  class FakeToastMark {
    constructor(markdown) { this.markdown = markdown; }
    getRootNode() { return root; }
  }
  const editor = { toastMark: { constructor: FakeToastMark } };
  expect(markdownForWysiwyg(editor, "alpha<br>beta")).toBe(`alpha${lineBreakMarker}beta`);
});

it("inserts a line-break widget at the WYSIWYG selection", () => {
  const widgetNode = { type: "widget" };
  const transaction = { replaceRangeWith: vi.fn(() => "transaction") };
  const state = {
    selection: { from: 4, to: 7 },
    schema: {
      nodes: {
        widget: { create: vi.fn(() => widgetNode) },
      },
      text: vi.fn((text) => text),
    },
    tr: transaction,
  };
  const dispatch = vi.fn();

  expect(insertWysiwygLineBreak({}, state, dispatch)).toBe(true);
  expect(state.schema.text).toHaveBeenCalledWith(`$$widget0 ${lineBreakMarker}$$`);
  expect(transaction.replaceRangeWith).toHaveBeenCalledWith(4, 7, widgetNode);
  expect(dispatch).toHaveBeenCalledWith("transaction");
});
