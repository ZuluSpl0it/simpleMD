const modeSelectors = {
  markdown: ".toastui-editor-md-container .ProseMirror",
  wysiwyg: ".toastui-editor-ww-container .toastui-editor-contents",
};

export function modeScrollElement(container, mode) {
  return container?.querySelector(modeSelectors[mode]) || null;
}

export function createScrollPositionListener(capture) {
  return () => capture();
}

function activeMode(container) {
  const main = container?.querySelector(".toastui-editor-main");
  if (main?.classList?.contains("toastui-editor-ww-mode")) return "wysiwyg";
  return "markdown";
}

function resolveView(container, view) {
  return view || activeMode(container);
}

function scrollElement(container, view) {
  if (view === "viewing") return container || null;
  return modeScrollElement(container, view);
}

export function readScrollPosition(container, view) {
  const resolvedView = resolveView(container, view);
  const target = scrollElement(container, resolvedView);
  const top = Math.max(0, Number(target?.scrollTop) || 0);
  const maximum = Math.max(0, (Number(target?.scrollHeight) || 0) - (Number(target?.clientHeight) || 0));
  return { view: resolvedView, top, ratio: maximum ? top / maximum : 0 };
}

function defaultSchedule(callback) {
  return globalThis.requestAnimationFrame?.(callback) || setTimeout(callback, 0);
}

function targetTop(position, view, target) {
  const top = Math.max(0, Number(position?.top) || 0);
  if (position?.view === view) return top;
  const ratio = Math.min(1, Math.max(0, Number(position?.ratio) || 0));
  const maximum = Math.max(0, (Number(target?.scrollHeight) || 0) - (Number(target?.clientHeight) || 0));
  return ratio * maximum;
}

export function restoreScrollPosition(container, view, position, schedule) {
  const resolvedView = resolveView(container, view);
  const run = schedule || defaultSchedule;
  let attempts = 0;
  const apply = () => {
    const target = scrollElement(container, resolvedView);
    const top = targetTop(position, resolvedView, target);
    if (target) target.scrollTop = top;
    attempts += 1;
    if (attempts < 4) run(apply);
  };
  run(apply);
}

export function preserveModeScroll(container, nextMode, cachedPosition, schedule, onPosition) {
  const previousMode = nextMode === "wysiwyg" ? "markdown" : "wysiwyg";
  const position = cachedPosition || readScrollPosition(container, previousMode);
  onPosition?.(position);
  restoreScrollPosition(container, nextMode, position, schedule);
}
