const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    minimize: () => ipcRenderer.send('window-minimize'),
    maximize: () => ipcRenderer.send('window-maximize'),
    close: () => ipcRenderer.send('window-close'),
    openExternal: (url) => ipcRenderer.send('open-external', url),
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),
    onUpdaterStatus: (callback) => ipcRenderer.on('updater-status', (event, data) => callback(data)),
    checkForUpdates: () => ipcRenderer.send('check-for-updates'),
    repairAndReinstall: () => ipcRenderer.send('repair-and-reinstall'),
    restartAndUpdate: () => ipcRenderer.send('restart-and-update')
});
