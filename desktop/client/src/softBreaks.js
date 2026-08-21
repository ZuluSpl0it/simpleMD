function isBreakTag(node) {
  return node?.type === "htmlInline" && /^<br\s*\/?\s*>$/i.test(node.literal || "");
}

const lineBreakWidgetInfo = "widget0";
export const lineBreakMarker = "\uE000simplemd-br\uE001";

function lineBreakWidgetContent() {
  return `$$${lineBreakWidgetInfo} ${lineBreakMarker}$$`;
}

export function encodeHtmlLineBreaks(markdown, rootNode) {
  const lineOffsets = [0];
  for (let index = 0; index < markdown.length; index += 1) {
    if (markdown[index] === "\n") lineOffsets.push(index + 1);
  }
  const replacements = [];
  const walker = rootNode?.walker?.();
  let event;
  while (walker && (event = walker.next())) {
    const node = event.node;
    if (!event.entering || !isBreakTag(node) || !node.sourcepos) continue;
    const [[startLine, startColumn], [endLine, endColumn]] = node.sourcepos;
    const start = lineOffsets[startLine - 1] + startColumn - 1;
    const end = lineOffsets[endLine - 1] + endColumn;
    if (markdown.slice(start, end) === node.literal) replacements.push({ start, end });
  }
  return replacements
    .sort((left, right) => right.start - left.start)
    .reduce(
      (result, { start, end }) => `${result.slice(0, start)}${lineBreakMarker}${result.slice(end)}`,
      markdown,
    );
}

export function decodeEditorLineBreaks(markdown) {
  return markdown
    .replace(new RegExp(`\\$\\$widget\\d+\\s+${lineBreakMarker}\\$\\$`, "g"), "<br>")
    .replaceAll(lineBreakMarker, "<br>");
}

export function markdownForWysiwyg(editor, markdown) {
  const ToastMark = editor?.toastMark?.constructor;
  if (!ToastMark) return markdown;
  const parsed = new ToastMark(markdown);
  return encodeHtmlLineBreaks(markdown, parsed.getRootNode());
}

export function insertWysiwygLineBreak(_payload, state, dispatch) {
  const widget = state.schema.nodes.widget.create(
    { info: lineBreakWidgetInfo },
    state.schema.text(lineBreakWidgetContent()),
  );
  if (dispatch) {
    const { from, to } = state.selection;
    dispatch(state.tr.replaceRangeWith(from, to, widget));
  }
  return true;
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
