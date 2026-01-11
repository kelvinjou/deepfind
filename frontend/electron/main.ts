import { app, BrowserWindow, dialog, ipcMain } from "electron";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { readdir, stat, readFile } from "node:fs/promises";
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.mjs
// │
process.env.APP_ROOT = path.join(__dirname, "..");

// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
export const VITE_DEV_SERVER_URL = process.env["VITE_DEV_SERVER_URL"];
export const MAIN_DIST = path.join(process.env.APP_ROOT, "dist-electron");
export const RENDERER_DIST = path.join(process.env.APP_ROOT, "dist");

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL
  ? path.join(process.env.APP_ROOT, "public")
  : RENDERER_DIST;

let win: BrowserWindow | null;

function createWindow() {
  win = new BrowserWindow({
    icon: path.join(process.env.VITE_PUBLIC, "electron-vite.svg"),
    webPreferences: {
      preload: path.join(__dirname, "preload.mjs"),
    },
  });

  // Test active push message to Renderer-process.
  win.webContents.on("did-finish-load", () => {
    win?.webContents.send("main-process-message", new Date().toLocaleString());
  });

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL);
  } else {
    // win.loadFile('dist/index.html')
    win.loadFile(path.join(RENDERER_DIST, "index.html"));
  }
}

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
    win = null;
  }
});

app.on("activate", () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
// IPC Handlers for file system operations
ipcMain.handle("dialog:openDirectory", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openDirectory"],
  });
  return result;
});

ipcMain.handle("dialog:openFile", async () => {
  const result = await dialog.showOpenDialog({
    properties: ["openFile"],
  });
  return result;
});

ipcMain.handle("fs:readDirectory", async (_event, dirPath: string) => {
  try {
    const files = await readdir(dirPath, { withFileTypes: true });
    return files.map((file) => ({
      name: file.name,
      isDirectory: file.isDirectory(),
    }));
  } catch (error) {
    throw new Error(`Failed to read directory: ${error}`);
  }
});

ipcMain.handle("fs:getStats", async (_event, filePath: string) => {
  try {
    const stats = await stat(filePath);
    return {
      isDirectory: stats.isDirectory(),
      isFile: stats.isFile(),
      size: stats.size,
      modified: stats.mtime,
    };
  } catch (error) {
    throw new Error(`Failed to get stats: ${error}`);
  }
});

ipcMain.handle("fs:readFile", async (_event, filePath: string) => {
  try {
    const content = await readFile(filePath, "utf-8");
    return content;
  } catch (error) {
    throw new Error(`Failed to read file: ${error}`);
  }
});

app.whenReady().then(createWindow);
