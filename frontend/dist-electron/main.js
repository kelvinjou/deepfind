import { app, BrowserWindow, ipcMain, dialog } from "electron";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { readdir, stat, readFile } from "node:fs/promises";
const __dirname$1 = path.dirname(fileURLToPath(import.meta.url));
process.env.APP_ROOT = path.join(__dirname$1, "..");
const VITE_DEV_SERVER_URL = process.env["VITE_DEV_SERVER_URL"];
const MAIN_DIST = path.join(process.env.APP_ROOT, "dist-electron");
const RENDERER_DIST = path.join(process.env.APP_ROOT, "dist");
process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL ? path.join(process.env.APP_ROOT, "public") : RENDERER_DIST;
let win;
function createWindow() {
  win = new BrowserWindow({
    icon: path.join(process.env.VITE_PUBLIC, "electron-vite.svg"),
    webPreferences: {
      preload: path.join(__dirname$1, "preload.mjs")
    }
  });
  win.webContents.on("did-finish-load", () => {
    win == null ? void 0 : win.webContents.send("main-process-message", (/* @__PURE__ */ new Date()).toLocaleString());
  });
  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(path.join(RENDERER_DIST, "index.html"));
  }
}
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
    win = null;
  }
});
app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
ipcMain.handle("dialog:openDirectory", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openDirectory"]
  });
  return result;
});
ipcMain.handle("dialog:openFile", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openFile"]
  });
  return result;
});
ipcMain.handle("fs:readDirectory", async (_event, dirPath) => {
  try {
    const files = await readdir(dirPath, { withFileTypes: true });
    return files.map((file) => ({
      name: file.name,
      isDirectory: file.isDirectory()
    }));
  } catch (error) {
    throw new Error(`Failed to read directory: ${error}`);
  }
});
ipcMain.handle("fs:getStats", async (_event, filePath) => {
  try {
    const stats = await stat(filePath);
    return {
      isDirectory: stats.isDirectory(),
      isFile: stats.isFile(),
      size: stats.size,
      modified: stats.mtime
    };
  } catch (error) {
    throw new Error(`Failed to get stats: ${error}`);
  }
});
ipcMain.handle("fs:readFile", async (_event, filePath) => {
  try {
    const content = await readFile(filePath, "utf-8");
    return content;
  } catch (error) {
    throw new Error(`Failed to read file: ${error}`);
  }
});
app.whenReady().then(createWindow);
export {
  MAIN_DIST,
  RENDERER_DIST,
  VITE_DEV_SERVER_URL
};
