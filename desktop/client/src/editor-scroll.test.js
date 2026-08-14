import { expect, it, vi } from "vitest";
import { createScrollPositionListener, preserveModeScroll, readScrollPosition, restoreScrollPosition } from "./editorScroll.js";

function surface(scrollTop, clientHeight, scrollHeight) {
  return { scrollTop, clientHeight, scrollHeight };
}

it("does not forward a DOM scroll event as saved position data", () => {
  const capture = vi.fn();
  const listener = createScrollPositionListener(capture);

  listener({ isTrusted: true });

  expect(capture).toHaveBeenCalledWith();
});

it("reads a proportional position from the currently visible editor surface", () => {
  const markdown = surface(900, 700, 9700);
  const wysiwyg = surface(48, 700, 7000);
  const main = { classList: { contains: (name) => name === "toastui-editor-md-mode" } };
  const container = {
    querySelector: vi.fn((selector) => {
      if (selector === ".toastui-editor-main") return main;
      return selector.includes("md-container") ? markdown : wysiwyg;
    }),
  };

  expect(readScrollPosition(container)).toEqual({ view: "markdown", top: 900, ratio: 0.1 });
});

it("uses the cached position captured before Toast UI resets the source surface", () => {
  const markdown = surface(0, 0, 0);
  const wysiwyg = surface(0, 700, 6700);
  const cached = { view: "markdown", top: 900, ratio: 0.1 };
  const container = {
    querySelector: vi.fn((selector) => selector.includes("md-container") ? markdown : wysiwyg),
  };
  const schedule = (callback) => callback();

  preserveModeScroll(container, "wysiwyg", cached, schedule);

  expect(wysiwyg.scrollTop).toBe(600);
});

it("reapplies the proportional position across layout and focus updates", () => {
  const target = surface(0, 200, 1200);
  const container = { querySelector: vi.fn(() => target) };
  const queue = [];
  const schedule = (callback) => queue.push(callback);

  restoreScrollPosition(container, "wysiwyg", { view: "markdown", top: 312, ratio: 0.5 }, schedule);
  queue.shift()();
  target.scrollTop = 999;
  while (queue.length) queue.shift()();

  expect(target.scrollTop).toBe(500);
});
