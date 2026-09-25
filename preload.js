const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    minimize: () => ipcRenderer.send('window-minimize'),
    maximize: () => ipcRenderer.send('window-maximize'),
    close: () => ipcRenderer.send('window-close'),
    openExternal: (url) => ipcRenderer.send('open-external', url),
    onUpdaterStatus: (callback) => ipcRenderer.on('updater-status', (event, data) => callback(data)),
    restartAndUpdate: () => ipcRenderer.send('restart-and-update')
});
