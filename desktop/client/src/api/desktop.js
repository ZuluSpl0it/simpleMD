function api() {
  if (!globalThis.pywebview?.api) {
    throw new Error("Flatnotes desktop bridge is not ready.");
  }
  return globalThis.pywebview.api;
}

export const searchWorkspace = (term) => api().search_workspace(term);
export const openMarkdown = () => api().open_markdown();
export const selectWorkspace = () => api().select_workspace();
export const saveTab = (tab) => api().save_tab(tab);
export const saveAs = (tab) => api().save_as(tab);
export const checkFile = (tab) => api().check_file(tab);
export const openDroppedPath = (path) => api().open_dropped_path(path);
export const getWorkspace = () => api().get_workspace();
