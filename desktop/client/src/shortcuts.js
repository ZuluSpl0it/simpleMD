export function isShortcut(event, code) {
  return Boolean((event?.ctrlKey || event?.metaKey) && event.code === code);
}
