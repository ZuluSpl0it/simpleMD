export function closeActions(tab) {
  return tab.dirty ? ["save", "discard", "cancel"] : [];
}
