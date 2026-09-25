const { app, BrowserWindow, ipcMain, shell, session } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const { autoUpdater } = require('electron-updater');

app.name = 'SteaMRogue';
app.commandLine.appendSwitch('disable-features', 'SpareRendererForSitePerProcess');

let backendProcess = null;
let mainWindow = null;
const BACKEND_PORT = 65012;

function startBackend() {
    console.log("Starting Python backend...");
    const env = { ...process.env, UV_SYSTEM_CERTS: 'true' };
    
    // Check if we are running from a packaged Electron app
    const isPackaged = app.isPackaged;
    
    if (isPackaged) {
        // When packaged, backend is compiled as SteamTools_Auto_Backend.exe
        const appDir = path.dirname(app.getPath('exe'));
        const backendExe = path.join(process.resourcesPath, 'SteamTools_Auto_Backend.exe');
        backendProcess = spawn(backendExe, [], {
            cwd: appDir,
            env: env,
            windowsHide: true
        });
    } else {
        // In development, run using 'uv' in shell
        backendProcess = spawn('uv', ['run', '--with-requirements', 'requirements.txt', 'python', 'app.py'], {
            cwd: __dirname,
            env: env,
            shell: true,
            windowsHide: false // Show python window console in dev for debugging
        });
    }
    
    backendProcess.stdout.on('data', (data) => {
        console.log(`Backend stdout: ${data}`);
    });
    backendProcess.stderr.on('data', (data) => {
        console.error(`Backend stderr: ${data}`);
    });
}

function createWindow() {
    // Clear cache to prevent loading old cached files
    session.defaultSession.clearCache().catch(err => {
        console.error("Failed to clear Electron cache:", err);
    });

    mainWindow = new BrowserWindow({
        width: 1150,
        height: 700,
        minWidth: 1000,
        minHeight: 650,
        resizable: true,
        frame: false, // Borderless window matching the Project Lightning style
        transparent: false,
        backgroundColor: '#0b0a11',
        show: false, // Don't show until ready-to-show
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: true
        }
    });

    // Intercept any new-window / target="_blank" links and open in default system browser
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    // Handle window drag/window actions in borderless custom header
    mainWindow.loadURL(`http://127.0.0.1:${BACKEND_PORT}/?v=${Date.now()}`);

    mainWindow.once('ready-to-show', () => {
        mainWindow.maximize();
        mainWindow.show();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// Window control events from preload bridge
ipcMain.on('window-minimize', () => {
    if (mainWindow) mainWindow.minimize();
});

ipcMain.on('window-maximize', () => {
    if (mainWindow) {
        if (mainWindow.isMaximized()) {
            mainWindow.unmaximize();
        } else {
            mainWindow.maximize();
        }
    }
});

ipcMain.on('window-close', () => {
    if (backendProcess) {
        if (process.platform === 'win32') {
            spawn('taskkill', ['/F', '/T', '/PID', backendProcess.pid]);
        } else {
            backendProcess.kill();
        }
    }
    app.quit();
});

// Open external URLs in default system browser
ipcMain.on('open-external', (event, url) => {
    shell.openExternal(url);
});

// Auto-Updater Logic (electron-updater)
autoUpdater.autoDownload = true;
autoUpdater.autoInstallOnAppQuit = true;

function setupAutoUpdater() {
    if (!app.isPackaged) return;

    autoUpdater.on('checking-for-update', () => {
        console.log('Checking for updates...');
    });

    autoUpdater.on('update-available', (info) => {
        console.log('Update available:', info.version);
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'available',
                version: info.version
            });
        }
    });

    autoUpdater.on('download-progress', (progress) => {
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'downloading',
                percent: Math.floor(progress.percent)
            });
        }
    });

    autoUpdater.on('update-downloaded', (info) => {
        console.log('Update downloaded:', info.version);
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'downloaded',
                version: info.version
            });
        }
    });

    autoUpdater.on('error', (err) => {
        console.error('AutoUpdater error:', err);
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'error',
                error: err == null ? "unknown" : (err.message || err).toString()
            });
        }
    });

    // Check for updates 5 seconds after startup
    setTimeout(() => {
        autoUpdater.checkForUpdatesAndNotify().catch(err => {
            console.error('Check for updates failed:', err);
        });
    }, 5000);
}

ipcMain.on('restart-and-update', () => {
    if (backendProcess) {
        if (process.platform === 'win32') {
            spawn('taskkill', ['/F', '/T', '/PID', backendProcess.pid]);
        } else {
            backendProcess.kill();
        }
    }
    autoUpdater.quitAndInstall();
});

app.whenReady().then(() => {
    startBackend();
    
    // Give backend 500ms to start before showing BrowserWindow (frontend retry loop will handle connectivity)
    setTimeout(createWindow, 500);

    // Initialize auto-updater
    setupAutoUpdater();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on('window-all-closed', () => {
    console.log("Electron windows closed. Terminating backend...");
    // Terminate python process
    if (backendProcess) {
        // On Windows, child process from shell might need taskkill to kill the entire process tree
        if (process.platform === 'win32') {
            spawn('taskkill', ['/F', '/T', '/PID', backendProcess.pid]);
        } else {
            backendProcess.kill();
        }
    }
    if (process.platform !== 'darwin') app.quit();
});
