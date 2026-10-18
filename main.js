const { app, BrowserWindow, ipcMain, shell, session, Tray, Menu } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const https = require('https');
const { spawn } = require('child_process');
const { autoUpdater } = require('electron-updater');

app.name = 'SteaMRogue';
app.commandLine.appendSwitch('disable-features', 'SpareRendererForSitePerProcess');
// Low-End PC & Legacy GPU (Intel HD Graphics) Optimization & Crash Resilience
app.commandLine.appendSwitch('disable-gpu-process-crash-limit');
app.commandLine.appendSwitch('js-flags', '--max-old-space-size=256');

// Graceful fallback for legacy GPU driver crashes
app.on('child-process-gone', (event, details) => {
    if (details.type === 'GPU') {
        console.warn(`[GPU Safety] GPU process exited (${details.reason}, code ${details.exitCode}). Safe software fallback engaged.`);
        try {
            app.disableHardwareAcceleration();
        } catch (e) {}
    }
});

let backendProcess = null;
let mainWindow = null;
let tray = null;
let isQuitting = false;
const BACKEND_PORT = 65012;

function findBackendExecutable() {
    const candidatePaths = [
        path.join(process.resourcesPath, 'SteamTools_Auto_Backend.exe'),
        path.join(path.dirname(app.getPath('exe')), 'resources', 'SteamTools_Auto_Backend.exe'),
        path.join(path.dirname(app.getPath('exe')), 'SteamTools_Auto_Backend.exe'),
        path.join(__dirname, 'SteamTools_Auto_Backend.exe'),
        path.join(__dirname, 'dist', 'SteamTools_Auto_Backend.exe'),
        path.join(__dirname, 'resources', 'SteamTools_Auto_Backend.exe')
    ];
    for (const p of candidatePaths) {
        if (p && fs.existsSync(p)) {
            return p;
        }
    }
    return null;
}

function terminateSteaMRogueAndHelpers() {
    isQuitting = true;
    if (process.platform === 'win32') {
        try {
            // 1. Close SteamTools companion app completely
            require('child_process').execSync('taskkill /F /IM SteamTools.exe', { stdio: 'ignore' });
        } catch (_) {}

        try {
            // 2. Kill Python backend process explicitly without /T so steam.exe is NEVER touched
            if (backendProcess && backendProcess.pid) {
                require('child_process').execSync(`taskkill /F /PID ${backendProcess.pid}`, { stdio: 'ignore' });
            }
        } catch (_) {}

        try {
            // 3. Clean up backend binary by image name
            require('child_process').execSync('taskkill /F /IM SteamTools_Auto_Backend.exe', { stdio: 'ignore' });
        } catch (_) {}
    } else {
        if (backendProcess) backendProcess.kill();
    }
}

function startBackend() {
    console.log("Starting Python backend...");
    try {
        require('child_process').execSync('taskkill /F /IM SteamTools_Auto_Backend.exe', { stdio: 'ignore' });
    } catch (_) {}
    const env = { ...process.env, UV_SYSTEM_CERTS: 'true' };
    
    const backendExe = findBackendExecutable();
    
    if (backendExe) {
        console.log(`Using compiled backend binary (Zero Dependency): ${backendExe}`);
        const appDir = path.dirname(backendExe);
        backendProcess = spawn(backendExe, [], {
            cwd: appDir,
            env: env,
            windowsHide: false
        });
    } else {
        console.log("No compiled backend binary found, falling back to python / uv (Dev Mode)...");
        const appPyPath = fs.existsSync(path.join(__dirname, 'backend', 'app.py'))
            ? path.join('backend', 'app.py')
            : 'app.py';
        const reqsPath = fs.existsSync(path.join(__dirname, 'backend', 'requirements.txt'))
            ? path.join('backend', 'requirements.txt')
            : 'requirements.txt';
        backendProcess = spawn('uv', ['run', '--with-requirements', reqsPath, 'python', appPyPath], {
            cwd: __dirname,
            env: env,
            shell: true,
            windowsHide: false
        });
    }
    
    backendProcess.stdout.on('data', (data) => {
        console.log(`Backend stdout: ${data}`);
    });
    backendProcess.stderr.on('data', (data) => {
        console.error(`Backend stderr: ${data}`);
    });
    backendProcess.on('error', (err) => {
        console.error(`Backend process failed to start:`, err);
    });
    backendProcess.on('exit', (code, signal) => {
        console.log(`Backend process exited with code ${code}, signal ${signal}`);
    });
}

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
    app.quit();
} else {
    app.on('second-instance', () => {
        if (mainWindow) {
            if (!mainWindow.isVisible()) mainWindow.show();
            if (mainWindow.isMinimized()) mainWindow.restore();
            mainWindow.focus();
        }
    });
}

function getAppIconPath() {
    const candidatePaths = [
        path.join(__dirname, 'icon.ico'),
        path.join(__dirname, 'build_tools', 'icon.ico'),
        path.join(__dirname, 'web', 'icon.ico'),
        path.join(process.resourcesPath, 'web', 'icon.ico'),
        path.join(process.resourcesPath, 'icon.ico')
    ];
    for (const p of candidatePaths) {
        if (p && fs.existsSync(p)) {
            return p;
        }
    }
    return path.join(__dirname, 'icon.ico');
}

let currentSystemMode = 'unlocked';
let currentAppLanguage = 'tr';

const trayTranslations = {
    tr: {
        tooltip: 'SteaMRogue — Yeni Nesil Steam Kiti',
        open: "⚡ SteaMRogue'u Aç",
        safeMode: '🛡️ Güvenli Mod (VAC Safe)',
        rogueMode: '⚡ SteaMRogue Modu',
        restartSteam: "🔄 Steam'i Yeniden Başlat",
        quit: '🎮 Tamamen Kapat (Sıfır RAM - Oyunlar Etkin Kalır)'
    },
    en: {
        tooltip: 'SteaMRogue — Next-Gen Steam Suite',
        open: '⚡ Open SteaMRogue',
        safeMode: '🛡️ Safe Mode (VAC Safe)',
        rogueMode: '⚡ SteaMRogue Mode',
        restartSteam: '🔄 Restart Steam',
        quit: '🎮 Fully Quit (Zero RAM - Games Remain Active)'
    }
};

function fetchSystemModeAndUpdateTray() {
    try {
        const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/api/system/mode`, (res) => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    if (parsed.success && parsed.mode) {
                        currentSystemMode = parsed.mode;
                        updateTrayContextMenu();
                    }
                } catch (_) {}
            });
        });
        req.on('error', () => {});
    } catch (_) {}
}

function switchSystemModeFromTray(targetMode) {
    try {
        const postData = JSON.stringify({ mode: targetMode });
        const req = http.request({
            hostname: '127.0.0.1',
            port: BACKEND_PORT,
            path: '/api/system/mode',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        }, (res) => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(data);
                    if (parsed.success && parsed.mode) {
                        currentSystemMode = parsed.mode;
                        updateTrayContextMenu();
                        if (mainWindow && !mainWindow.isDestroyed()) {
                            mainWindow.webContents.send('system-mode-changed', parsed.mode);
                        }
                    }
                } catch (_) {}
            });
        });
        req.on('error', (err) => console.warn('[Tray] switch mode error:', err));
        req.write(postData);
        req.end();
    } catch (e) {
        console.warn('[Tray] switch mode exception:', e);
    }
}

function updateTrayContextMenu() {
    if (!tray) return;
    const isSafe = (currentSystemMode === 'safe');
    const strings = trayTranslations[currentAppLanguage] || trayTranslations.tr;

    try {
        tray.setToolTip(strings.tooltip);
    } catch (_) {}

    const contextMenu = Menu.buildFromTemplate([
        {
            label: strings.open,
            click: () => {
                if (mainWindow) {
                    mainWindow.show();
                    if (mainWindow.isMinimized()) mainWindow.restore();
                    mainWindow.focus();
                }
            }
        },
        { type: 'separator' },
        {
            label: `${strings.safeMode}${isSafe ? '  ✓' : ''}`,
            type: 'radio',
            checked: isSafe,
            click: () => switchSystemModeFromTray('safe')
        },
        {
            label: `${strings.rogueMode}${!isSafe ? '  ✓' : ''}`,
            type: 'radio',
            checked: !isSafe,
            click: () => switchSystemModeFromTray('unlocked')
        },
        { type: 'separator' },
        {
            label: strings.restartSteam,
            click: () => {
                try {
                    const postData = JSON.stringify({ force: false });
                    const req = http.request({
                        hostname: '127.0.0.1',
                        port: BACKEND_PORT,
                        path: '/api/restart_steam',
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Content-Length': Buffer.byteLength(postData)
                        }
                    }, (res) => {
                        console.log(`[Tray] Restart Steam response status: ${res.statusCode}`);
                    });
                    req.on('error', (err) => {
                        console.warn('[Tray] Restart Steam request error:', err.message);
                    });
                    req.write(postData);
                    req.end();
                } catch (e) {
                    console.warn('[Tray] Failed to request restart_steam:', e);
                }
            }
        },
        { type: 'separator' },
        {
            label: strings.quit,
            click: () => {
                terminateSteaMRogueAndHelpers();
                if (mainWindow) {
                    mainWindow.destroy();
                }
                app.quit();
            }
        }
    ]);

    tray.setContextMenu(contextMenu);
}

function createTray() {
    if (tray) return;
    try {
        const iconPath = getAppIconPath();
        tray = new Tray(iconPath);
        const strings = trayTranslations[currentAppLanguage] || trayTranslations.tr;
        tray.setToolTip(strings.tooltip);

        updateTrayContextMenu();
        fetchSystemModeAndUpdateTray();

        tray.on('click', () => {
            if (mainWindow) {
                if (!mainWindow.isVisible()) {
                    mainWindow.show();
                }
                if (mainWindow.isMinimized()) mainWindow.restore();
                mainWindow.focus();
            }
        });

        tray.on('double-click', () => {
            if (mainWindow) {
                if (!mainWindow.isVisible()) {
                    mainWindow.show();
                }
                if (mainWindow.isMinimized()) mainWindow.restore();
                mainWindow.focus();
            }
        });

        tray.on('right-click', () => {
            fetchSystemModeAndUpdateTray();
        });
    } catch (err) {
        console.error('[Tray] Failed to initialize tray:', err);
    }
}

ipcMain.on('mode-changed-in-ui', (event, mode) => {
    currentSystemMode = mode;
    updateTrayContextMenu();
});

ipcMain.on('language-changed-in-ui', (event, lang) => {
    if (lang === 'tr' || lang === 'en') {
        currentAppLanguage = lang;
        updateTrayContextMenu();
    }
});

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1150,
        height: 700,
        minWidth: 1000,
        minHeight: 650,
        resizable: true,
        frame: false, // Borderless window matching the Project Lightning style
        transparent: false,
        backgroundColor: '#090a10',
        show: false,
        icon: getAppIconPath(),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true,
            sandbox: true
        }
    });

    // Show window immediately once ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.maximize();
        mainWindow.show();
    });

    // Intercept any new-window / target="_blank" links and open in default system browser
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    // Intercept close event: hide to system tray instead of destroying
    mainWindow.on('close', (event) => {
        if (!isQuitting) {
            event.preventDefault();
            mainWindow.hide();
            return false;
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function loadAppUI() {
    if (!mainWindow || mainWindow.isDestroyed()) return;
    try {
        mainWindow.webContents.session.clearCache().catch(() => {});
    } catch (_) {}
    const targetUrl = `http://127.0.0.1:${BACKEND_PORT}/?v=${Date.now()}`;

    // Auto-retry on failed load so slow machine startup never results in a blank/error screen
    const failHandler = (event, errorCode, errorDescription) => {
        console.warn(`Page load failed (${errorCode}: ${errorDescription}). Retrying in 500ms...`);
        setTimeout(() => {
            if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.loadURL(targetUrl).catch(() => {});
            }
        }, 500);
    };

    mainWindow.webContents.once('did-fail-load', failHandler);
    mainWindow.webContents.once('did-finish-load', () => {
        mainWindow.webContents.removeListener('did-fail-load', failHandler);
    });

    mainWindow.loadURL(targetUrl).catch(() => {});
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
    if (mainWindow) {
        mainWindow.hide();
    }
});

// Open external URLs in default system browser
ipcMain.on('open-external', (event, url) => {
    shell.openExternal(url);
});

// Auto-Updater Logic (electron-updater + Hybrid Hotfix / Repair Support)
autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = false;

function ensureWebAssets() {
    try {
        const webDest = path.join(process.resourcesPath, 'web');
        const indexHtmlDest = path.join(webDest, 'index.html');
        if (!fs.existsSync(indexHtmlDest)) {
            console.warn(`[Self-Healing] ${indexHtmlDest} not found. Attempting recovery...`);
            const possibleSources = [
                path.join(__dirname, 'web'),
                path.join(app.getAppPath(), 'web'),
                path.join(process.resourcesPath, 'web'),
                path.join(path.dirname(process.resourcesPath), 'web')
            ];
            for (const src of possibleSources) {
                if (fs.existsSync(path.join(src, 'index.html'))) {
                    fs.cpSync(src, webDest, { recursive: true });
                    console.log(`[Self-Healing] Successfully restored web assets from ${src}`);
                    break;
                }
            }
        }
    } catch (err) {
        console.error('[Self-Healing] Error ensuring web assets:', err);
    }
}

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

function fetchJson(url) {
    return new Promise((resolve) => {
        https.get(url, { headers: { 'User-Agent': 'SteaMRogue-App' } }, (res) => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                return fetchJson(res.headers.location).then(resolve);
            }
            if (res.statusCode !== 200) return resolve(null);
            let raw = '';
            res.on('data', chunk => raw += chunk);
            res.on('end', () => {
                try { resolve(JSON.parse(raw)); } catch { resolve(null); }
            });
        }).on('error', () => resolve(null));
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
                message: 'GitHub üzerinden en güncel kurulum paketi sorgulanıyor ve indiriliyor...'
            });
        }

        // Dynamically resolve release asset from GitHub API so version changes never 404
        const releaseData = await fetchJson('https://api.github.com/repos/mythoscd/SteaMRogue/releases/latest');
        let downloadUrl = null;
        let latestVersion = app.getVersion();
        if (releaseData && releaseData.assets && releaseData.assets.length > 0) {
            latestVersion = (releaseData.tag_name || '').replace(/^v/i, '') || latestVersion;
            const exeAsset = releaseData.assets.find(a => a.name.endsWith('.exe') && !a.name.toLowerCase().includes('backend'));
            if (exeAsset && exeAsset.browser_download_url) {
                downloadUrl = exeAsset.browser_download_url;
            }
        }
        if (!downloadUrl) {
            downloadUrl = `https://github.com/mythoscd/SteaMRogue/releases/latest/download/SteaMRogue-Setup-${latestVersion}.exe`;
        }

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
    terminateSteaMRogueAndHelpers();
    if (downloadedInstallerPath && fs.existsSync(downloadedInstallerPath)) {
        spawn(downloadedInstallerPath, [], { detached: true, stdio: 'ignore' }).unref();
        app.quit();
    } else {
        autoUpdater.quitAndInstall();
    }
});

function waitForBackendAndLoad(maxRetries = 350, retryInterval = 100) {
    let attempts = 0;
    let loaded = false;
    
    function checkBackend() {
        if (loaded) return;
        attempts++;
        const req = http.get(`http://127.0.0.1:${BACKEND_PORT}/api/status`, (res) => {
            if (res.statusCode === 200 || res.statusCode === 304) {
                console.log(`Backend is ready after ${attempts * retryInterval}ms. Loading UI...`);
                loaded = true;
                loadAppUI();
            } else {
                if (attempts < maxRetries && !loaded) {
                    setTimeout(checkBackend, retryInterval);
                } else if (!loaded) {
                    console.warn("Backend took too long to return 200. Loading UI anyway.");
                    loaded = true;
                    loadAppUI();
                }
            }
        });
        
        req.on('error', () => {
            if (attempts < maxRetries && !loaded) {
                setTimeout(checkBackend, retryInterval);
            } else if (!loaded) {
                console.warn("Backend connection attempts exhausted. Loading UI anyway.");
                loaded = true;
                loadAppUI();
            }
        });
        
        req.setTimeout(250, () => {
            req.destroy();
        });
    }
    
    // Begin pinging immediately (after 30ms)
    setTimeout(checkBackend, 30);
}

app.whenReady().then(() => {
    // 0. Ensure web assets exist (self-healing if updater wiped them)
    ensureWebAssets();

    // 1. Create native window immediately (0ms user click feedback)
    createWindow();

    // 2. Initialize system tray
    createTray();

    // 3. Start Python backend
    startBackend();
    
    // 4. Ultra-fast backend polling (80ms) and load UI instantly
    waitForBackendAndLoad();

    // 5. Initialize auto-updater in background
    setupAutoUpdater();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
            loadAppUI();
        }
    });
});

app.on('before-quit', () => {
    isQuitting = true;
});

app.on('window-all-closed', () => {
    if (isQuitting) {
        console.log("Electron windows closed and isQuitting set. Terminating backend...");
        terminateSteaMRogueAndHelpers();
        if (process.platform !== 'darwin') app.quit();
    }
});

app.on('will-quit', () => {
    terminateSteaMRogueAndHelpers();
});
