const ready = new Promise((resolve) => {
  if (globalThis.pywebview?.api) resolve(globalThis.pywebview.api);
  else window.addEventListener("pywebviewready", () => resolve(globalThis.pywebview.api), { once: true });
});
const call = (name, ...args) => ready.then((bridge) => bridge[name](...args));

export const searchWorkspace = (term) => call("search_workspace", term);
export const rebuildIndex = () => call("rebuild_index");
export const getIndexStatus = () => call("get_index_status");
export const openMarkdown = () => call("open_markdown");
export const selectWorkspace = () => call("select_workspace");
export const saveTab = (tab) => call("save_tab", tab);
export const saveAs = (tab) => call("save_as", tab);
export const checkFile = (tab) => call("check_file", tab);
export const openDroppedPath = (path) => call("open_dropped_path", path);
export const getWorkspace = () => call("get_workspace");
export const createWorkspaceNote = (title, content) => call("create_workspace_note", title, content);
export const renameWorkspaceNote = (title, newTitle) => call("rename_workspace_note", title, newTitle);
export const deleteWorkspaceNote = (title) => call("delete_workspace_note", title);
export const startupEvent = (event) => call("startup_event", event);
export const getTheme = () => call("get_theme");
export const setTheme = (theme) => call("set_theme", theme);
export const getFontSettings = () => call("get_font_settings");
export const getHeadingColors = () => call("get_heading_colors");
