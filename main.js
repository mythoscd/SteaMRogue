const { app, BrowserWindow, ipcMain, shell, session } = require('electron');
const path = require('path');
const fs = require('fs');
const https = require('https');
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

// Auto-Updater Logic (electron-updater + Hybrid Hotfix / Repair Support)
autoUpdater.autoDownload = true;
autoUpdater.autoInstallOnAppQuit = true;

function getMetaFilePath() {
    return path.join(app.getPath('userData'), 'installed-build-meta.json');
}

function getLocalBuildMeta() {
    try {
        const p = getMetaFilePath();
        if (fs.existsSync(p)) {
            return JSON.parse(fs.readFileSync(p, 'utf8'));
        }
    } catch (e) {
        console.error('Error reading build meta:', e);
    }
    let mtime = new Date(0).toISOString();
    try {
        mtime = fs.statSync(process.execPath).mtime.toISOString();
    } catch (e) {}
    return {
        version: app.getVersion(),
        installedAt: mtime,
        sha512: null
    };
}

function saveLocalBuildMeta(meta) {
    try {
        fs.writeFileSync(getMetaFilePath(), JSON.stringify(meta, null, 2), 'utf8');
    } catch (e) {
        console.error('Error saving build meta:', e);
    }
}

function downloadFile(url, destPath, onProgress) {
    return new Promise((resolve, reject) => {
        const request = (targetUrl) => {
            const req = https.get(targetUrl, {
                headers: { 'User-Agent': 'SteaMRogue-App' }
            }, (res) => {
                if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                    return request(res.headers.location);
                }
                if (res.statusCode !== 200) {
                    return reject(new Error(`İndirme başarısız (HTTP ${res.statusCode})`));
                }
                const totalBytes = parseInt(res.headers['content-length'] || '0', 10);
                let receivedBytes = 0;
                const fileStream = fs.createWriteStream(destPath);
                res.on('data', (chunk) => {
                    receivedBytes += chunk.length;
                    if (totalBytes > 0 && typeof onProgress === 'function') {
                        const percent = Math.floor((receivedBytes / totalBytes) * 100);
                        onProgress(percent, receivedBytes, totalBytes);
                    }
                });
                res.pipe(fileStream);
                fileStream.on('finish', () => {
                    fileStream.close(() => resolve(destPath));
                });
                fileStream.on('error', (err) => {
                    fs.unlink(destPath, () => {});
                    reject(err);
                });
            });
            req.on('error', reject);
        };
        request(url);
    });
}

let isRepairing = false;
let downloadedInstallerPath = null;

async function runRepairDownload() {
    if (isRepairing) return;
    isRepairing = true;

    try {
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'downloading',
                percent: 0,
                message: 'GitHub üzerinden en güncel kurulum paketi indiriliyor...'
            });
        }

        const downloadUrl = `https://github.com/mythoscd/SteaMRogue/releases/latest/download/SteaMRogue-Setup-${app.getVersion()}.exe`;
        const tempDest = path.join(app.getPath('temp'), `SteaMRogue-Setup-Latest.exe`);

        await downloadFile(downloadUrl, tempDest, (percent) => {
            if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('updater-status', {
                    status: 'downloading',
                    percent: percent
                });
            }
        });

        downloadedInstallerPath = tempDest;
        isRepairing = false;

        saveLocalBuildMeta({
            version: app.getVersion(),
            installedAt: new Date().toISOString(),
            sha512: null
        });

        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'downloaded',
                version: app.getVersion(),
                isRepair: true
            });
        }
    } catch (err) {
        isRepairing = false;
        console.error('Repair download failed:', err);
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'error',
                error: (err && err.message) || err.toString()
            });
        }
    }
}

function setupAutoUpdater() {
    if (!app.isPackaged) return;

    autoUpdater.on('checking-for-update', () => {
        console.log('Checking for updates...');
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'checking'
            });
        }
    });

    autoUpdater.on('update-available', (info) => {
        console.log('Update available (new version):', info.version);
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'available',
                version: info.version
            });
        }
    });

    autoUpdater.on('update-not-available', (info) => {
        console.log('Update not available via semver. Checking releaseDate & sha...', info.version);
        const localMeta = getLocalBuildMeta();
        const remoteReleaseDate = info && info.releaseDate ? new Date(info.releaseDate).getTime() : 0;
        const localInstallDate = localMeta && localMeta.installedAt ? new Date(localMeta.installedAt).getTime() : 0;
        const remoteSha = (info && (info.sha512 || (info.files && info.files[0] && info.files[0].sha512))) || null;

        // If remote release on GitHub is newer by > 2 minutes than local install OR sha512 changed
        const isNewerHotfix = (remoteReleaseDate > (localInstallDate + 120000)) || (remoteSha && localMeta.sha512 && remoteSha !== localMeta.sha512);

        if (isNewerHotfix) {
            console.log('Hotfix / re-release detected on GitHub for version:', info.version);
            if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('updater-status', {
                    status: 'hotfix-available',
                    version: info.version,
                    releaseDate: info.releaseDate,
                    message: `v${info.version} için GitHub'da yeni bir düzeltme/güncelleme paketi yayınlandı.`
                });
            }
        } else {
            if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('updater-status', {
                    status: 'not-available',
                    version: info.version
                });
            }
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
        saveLocalBuildMeta({
            version: info.version,
            installedAt: new Date().toISOString(),
            sha512: info.sha512 || (info.files && info.files[0] && info.files[0].sha512) || null
        });
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

// IPC Handlers
ipcMain.handle('get-app-version', () => app.getVersion());

ipcMain.on('check-for-updates', () => {
    if (!app.isPackaged) {
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'dev-mode',
                message: 'Geliştirici modundasınız. Otomatik güncelleme kurulu uygulamada çalışır.'
            });
        }
        return;
    }
    autoUpdater.checkForUpdates().catch(err => {
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'error',
                error: (err && err.message) || err.toString()
            });
        }
    });
});

ipcMain.on('repair-and-reinstall', () => {
    if (!app.isPackaged) {
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('updater-status', {
                status: 'dev-mode',
                message: 'Geliştirici modundasınız. Onar ve yeniden kur işlemi kurulu sürümde çalışır.'
            });
        }
        return;
    }
    runRepairDownload();
});

ipcMain.on('restart-and-update', () => {
    if (backendProcess) {
        if (process.platform === 'win32') {
            spawn('taskkill', ['/F', '/T', '/PID', backendProcess.pid]);
        } else {
            backendProcess.kill();
        }
    }
    if (downloadedInstallerPath && fs.existsSync(downloadedInstallerPath)) {
        spawn(downloadedInstallerPath, [], { detached: true, stdio: 'ignore' }).unref();
        app.quit();
    } else {
        autoUpdater.quitAndInstall();
    }
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
