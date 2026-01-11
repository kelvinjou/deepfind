"use strict";
const electron = require("electron");
electron.contextBridge.exposeInMainWorld("ipcRenderer", {
  on(...args) {
    const [channel, listener] = args;
    return electron.ipcRenderer.on(channel, (event, ...args2) => listener(event, ...args2));
  },
  off(...args) {
    const [channel, ...omit] = args;
    return electron.ipcRenderer.off(channel, ...omit);
  },
  send(...args) {
    const [channel, ...omit] = args;
    return electron.ipcRenderer.send(channel, ...omit);
  },
  invoke(...args) {
    const [channel, ...omit] = args;
    return electron.ipcRenderer.invoke(channel, ...omit);
  }
});
electron.contextBridge.exposeInMainWorld("electronAPI", {
  openDirectory: () => electron.ipcRenderer.invoke("dialog:openDirectory"),
  openFile: () => electron.ipcRenderer.invoke("dialog:openFile"),
  readDirectory: (dirPath) => electron.ipcRenderer.invoke("fs:readDirectory", dirPath),
  getStats: (filePath) => electron.ipcRenderer.invoke("fs:getStats", filePath),
  readFile: (filePath) => electron.ipcRenderer.invoke("fs:readFile", filePath)
});
