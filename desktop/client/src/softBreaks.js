function isBreakTag(node) {
  return node?.type === "htmlInline" && /<br\s*\/?\s*>/i.test(node.literal || "");
}

export function configureWysiwygSoftBreaks(editor) {
  const convertors = editor?.convertor?.toWwConvertors;
  if (!convertors || typeof convertors.softbreak !== "function") return false;

  convertors.softbreak = (state, node) => {
    if (node?.parent?.type !== "paragraph") return;
    if (node.prev && !isBreakTag(node.prev)) {
      const current = state.top?.();
      if (current?.type?.name === "paragraph") {
        current.attrs ||= {};
        current.attrs.classNames = [
          ...(current.attrs.classNames || []),
          "flatnotes-softbreak-before",
        ];
      }
      state.closeNode();
    }
    if (node.next && !isBreakTag(node.next)) {
      state.openNode(state.schema.nodes.paragraph, {
        classNames: ["flatnotes-softbreak"],
      });
    }
  };
  return true;
}
