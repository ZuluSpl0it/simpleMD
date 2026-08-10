export function conflictActions(tab) {
  if (tab.externalState === "missing") return ["saveAs"];
  return tab.dirty ? ["reload", "overwrite", "saveAs"] : ["reload"];
}
