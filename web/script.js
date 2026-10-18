/* ==========================================================================
   Project Lightning GUI Frontend Script
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // === 0. APP STARTUP SPLASH SCREEN CONTROLLER ===
    const splashScreen = document.getElementById("app-splash-screen");
    const splashProgressBar = document.getElementById("splash-progress-bar");
    const splashStatusText = document.getElementById("splash-status-text");

    let splashDismissed = false;
    function dismissSplashScreen() {
        if (splashDismissed || !splashScreen) return;
        splashDismissed = true;
        if (splashProgressBar) splashProgressBar.style.width = "100%";
        if (splashStatusText) {
            splashStatusText.innerHTML = '<i class="fa-solid fa-check" style="color: #10b981;"></i> Sistem hazır, kütüphaneye bağlanıldı.';
        }
        setTimeout(() => {
            splashScreen.classList.add("hidden");
            setTimeout(() => {
                initDisclaimerModal();
            }, 250);
        }, 300);
    }

    // === 0.1 FIRST LAUNCH DISCLAIMER & EULA CONTROLLER (10s COUNTDOWN) ===
    function initDisclaimerModal(force = false) {
        const STORAGE_KEY = "steamrogue_eula_accepted_v1_1_8";
        try {
            if (!force && localStorage.getItem(STORAGE_KEY) === "true") {
                return;
            }
        } catch (e) {
            console.warn("localStorage check failed:", e);
        }

        const modal = document.getElementById("disclaimer-modal");
        const acceptBtn = document.getElementById("btn-accept-disclaimer");
        const countdownSpan = document.getElementById("disclaimer-countdown-text");
        const btnIcon = document.getElementById("disclaimer-btn-icon");
        const closeBtn = document.getElementById("disclaimer-modal-close");

        if (!modal || !acceptBtn || !countdownSpan) return;

        modal.style.display = "flex";
        modal.classList.add("active");

        const closeModal = () => {
            if (window._disclaimerTimer) clearInterval(window._disclaimerTimer);
            modal.classList.remove("active");
            modal.style.display = "none";
        };

        if (force) {
            // Manual review from settings: show instantly with close button, no countdown
            if (window._disclaimerTimer) clearInterval(window._disclaimerTimer);
            if (closeBtn) {
                closeBtn.style.display = "block";
                closeBtn.onclick = closeModal;
            }
            acceptBtn.disabled = false;
            acceptBtn.classList.add("active-ready");
            if (btnIcon) btnIcon.className = "fa-solid fa-check";
            countdownSpan.textContent = "Kapat";
            acceptBtn.onclick = closeModal;
            modal.onclick = (e) => {
                if (e.target === modal) closeModal();
            };
            return;
        }

        // First launch: enforce 10s countdown
        if (closeBtn) closeBtn.style.display = "none";
        modal.onclick = null;
        let secondsLeft = 10;
        acceptBtn.disabled = true;
        acceptBtn.classList.remove("active-ready");
        if (btnIcon) btnIcon.className = "fa-solid fa-hourglass-half";
        countdownSpan.textContent = `Şartları Okudum ve Kabul Ediyorum (${secondsLeft})`;

        if (window._disclaimerTimer) clearInterval(window._disclaimerTimer);
        window._disclaimerTimer = setInterval(() => {
            secondsLeft--;
            if (secondsLeft > 0) {
                countdownSpan.textContent = `Şartları Okudum ve Kabul Ediyorum (${secondsLeft})`;
            } else {
                clearInterval(window._disclaimerTimer);
                acceptBtn.disabled = false;
                acceptBtn.classList.add("active-ready");
                if (btnIcon) {
                    btnIcon.className = "fa-solid fa-check";
                }
                countdownSpan.textContent = "Şartları Kabul Ediyorum ve Devam Et";
            }
        }, 1000);

        acceptBtn.onclick = () => {
            if (secondsLeft > 0) return;
            try {
                localStorage.setItem(STORAGE_KEY, "true");
            } catch (e) {
                console.warn("localStorage save failed:", e);
            }
            closeModal();
        };

        // Block ESC key from dismissing unaccepted disclaimer
        window.addEventListener("keydown", (e) => {
            if (modal.classList.contains("active") && e.key === "Escape") {
                if (force) {
                    closeModal();
                } else {
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        }, true);
    }
    window.showDisclaimerModal = () => initDisclaimerModal(true);

    if (splashScreen) {
        setTimeout(() => {
            if (splashProgressBar && !splashDismissed) splashProgressBar.style.width = "45%";
            if (splashStatusText && !splashDismissed) {
                splashStatusText.innerHTML = '<i class="fa-solid fa-arrows-rotate fa-spin" style="color: #38bdf8;"></i> Kilit açıcılar ve manifest depoları eşitleniyor...';
            }
        }, 450);

        setTimeout(() => {
            if (splashProgressBar && !splashDismissed) splashProgressBar.style.width = "80%";
            if (splashStatusText && !splashDismissed) {
                splashStatusText.innerHTML = '<i class="fa-solid fa-fingerprint" style="color: #c084fc;"></i> İmzalar ve bypass listesi doğrulanıyor...';
            }
        }, 950);

        // Safety fallback: always reveal app after max 2.2s so user is never blocked
        setTimeout(() => {
            dismissSplashScreen();
        }, 2200);
    }

    // CUSTOM ALERT / CONFIRM GLOBAL OVERRIDES
    function showCustomAlert(message, title = "SteaMRogue") {
        return new Promise((resolve) => {
            const modal = document.getElementById("custom-alert-modal");
            const msgEl = document.getElementById("custom-modal-message");
            const btnConfirm = document.getElementById("custom-alert-confirm");
            const btnCancel = document.getElementById("custom-alert-cancel");
            const btnClose = document.getElementById("custom-alert-close");
            const titleEl = document.getElementById("custom-modal-title");

            if (titleEl) titleEl.textContent = title || "SteaMRogue";
            if (msgEl) msgEl.textContent = message;
            if (btnCancel) btnCancel.style.display = "none";
            if (btnConfirm) btnConfirm.textContent = "Tamam";

            if (modal) modal.classList.add("active");

            const close = () => {
                if (modal) modal.classList.remove("active");
                if (btnConfirm) btnConfirm.removeEventListener("click", onOk);
                if (btnClose) btnClose.removeEventListener("click", close);
                resolve();
            };

            const onOk = () => {
                close();
            };

            if (btnConfirm) btnConfirm.addEventListener("click", onOk);
            if (btnClose) btnClose.addEventListener("click", close);
        });
    }

    function showCustomConfirm(message, title = "Onay Gerekli", okText = "Tamam", cancelText = "İptal") {
        return new Promise((resolve) => {
            const modal = document.getElementById("custom-alert-modal");
            const msgEl = document.getElementById("custom-modal-message");
            const btnConfirm = document.getElementById("custom-alert-confirm");
            const btnCancel = document.getElementById("custom-alert-cancel");
            const btnClose = document.getElementById("custom-alert-close");
            const titleEl = document.getElementById("custom-modal-title");

            if (titleEl) titleEl.textContent = title || "Onay Gerekli";
            if (msgEl) msgEl.textContent = message;
            if (btnCancel) {
                btnCancel.style.display = "block";
                btnCancel.textContent = cancelText || "İptal";
            }
            if (btnConfirm) btnConfirm.textContent = okText || "Tamam";

            if (modal) modal.classList.add("active");

            const cleanup = () => {
                if (modal) modal.classList.remove("active");
                if (btnConfirm) btnConfirm.removeEventListener("click", onYes);
                if (btnCancel) btnCancel.removeEventListener("click", onNo);
                if (btnClose) btnClose.removeEventListener("click", onNo);
            };

            const onYes = () => {
                cleanup();
                resolve(true);
            };

            const onNo = () => {
                cleanup();
                resolve(false);
            };

            if (btnConfirm) btnConfirm.addEventListener("click", onYes);
            if (btnCancel) btnCancel.addEventListener("click", onNo);
            if (btnClose) btnClose.addEventListener("click", onNo);
        });
    }

    window.alert = showCustomAlert;
    window.showCustomAlert = showCustomAlert;
    window.confirm = showCustomConfirm;
    window.showCustomConfirm = showCustomConfirm;

    // 1. CLOCK LOGIC
    initClock();

    // 2. TAB CONTROLLER
    initTabs();

    // 3. API & DATA CONTROLLERS
    initAppLogic();

    // 4. SAM (STEAM ACHIEVEMENT MANAGER) CONTROLLER
    initSAM();

    // 5. AUTOMATIC STARTUP HEALTH CHECK & DIAGNOSTICS
    setTimeout(checkStartupHealth, 500);

    // Sync version badge dynamically from Electron core or backend
    const updateVersionBadges = (ver) => {
        if (!ver) return;
        const cleanVer = ver.replace(/^v/, '');
        const topBadge = document.getElementById("app-version-badge") || document.querySelector('.version-badge');
        if (topBadge) topBadge.textContent = `v${cleanVer}`;
        const settingsBadge = document.getElementById("settings-app-version-badge");
        if (settingsBadge) settingsBadge.textContent = `v${cleanVer}`;
        const splashBadge = document.querySelector('.splash-version-pill');
        if (splashBadge) splashBadge.textContent = `v${cleanVer} • Yeni Nesil Steam Kiti`;
    };

    if (window.electronAPI && typeof window.electronAPI.getAppVersion === 'function') {
        window.electronAPI.getAppVersion().then(updateVersionBadges).catch(() => {});
    } else {
        fetch('/api/health')
            .then(r => r.json())
            .then(data => {
                if (data && data.version) updateVersionBadges(data.version);
            })
            .catch(() => {});
    }

    requestAnimationFrame(() => {
        if (window.electronAPI && window.electronAPI.sendRendererReady) {
            window.electronAPI.sendRendererReady();
        }
    });
});

// %% Automatic Startup System Health Check & Forced Repair Modal
async function checkStartupHealth() {
    try {
        const res = await fetch("/api/diagnose_system");
        const data = await res.json();
        if (data && data.has_issues && Array.isArray(data.issues) && data.issues.length > 0) {
            showForcedHealthModal(data.issues);
        }
    } catch (e) {
        console.debug("[Health Check] Diagnostic probe:", e);
    }
}

function showForcedHealthModal(issues) {
    const modal = document.getElementById("health-warning-modal");
    const list = document.getElementById("health-issues-list");
    const btnRepair = document.getElementById("btn-health-repair");
    if (!modal || !list || !btnRepair) return;

    list.innerHTML = "";
    issues.forEach(issue => {
        const li = document.createElement("li");
        li.style.cssText = "display: flex; align-items: flex-start; gap: 10px; color: #fca5a5; font-size: 0.86rem; line-height: 1.4; background: rgba(239, 68, 68, 0.08); padding: 8px 12px; border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.15);";
        
        const icon = document.createElement("i");
        icon.className = "fa-solid fa-circle-exclamation";
        icon.style.cssText = "margin-top: 2px; color: #ef4444; flex-shrink: 0; font-size: 0.95rem;";
        
        const span = document.createElement("span");
        span.textContent = issue;
        
        li.appendChild(icon);
        li.appendChild(span);
        list.appendChild(li);
    });

    modal.classList.add("active");

    // Block ESC key and backdrop clicks from closing the modal (forced repair)
    const blockEscHandler = (e) => {
        if (modal.classList.contains("active") && e.key === "Escape") {
            e.preventDefault();
            e.stopPropagation();
        }
    };
    window.addEventListener("keydown", blockEscHandler, true);

    modal.onclick = (e) => {
        if (e.target === modal) {
            e.stopPropagation();
            e.preventDefault();
        }
    };

    btnRepair.onclick = async () => {
        btnRepair.disabled = true;
        btnRepair.style.filter = "brightness(0.9)";
        btnRepair.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sistem Onarılıyor... Lütfen Bekleyin';

        try {
            const res = await fetch("/api/self_heal", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ force: true, restart_steam: false })
            });
            const data = await res.json();
            
            if (data && data.ok) {
                btnRepair.style.background = "linear-gradient(135deg, #10b981, #059669)";
                btnRepair.style.borderColor = "#059669";
                btnRepair.style.color = "#ffffff";
                btnRepair.innerHTML = '<i class="fa-solid fa-circle-check"></i> Tüm Sorunlar Başarıyla Onarıldı!';

                setTimeout(() => {
                    modal.classList.remove("active");
                    window.removeEventListener("keydown", blockEscHandler, true);
                    const healBadge = document.getElementById("self-heal-badge");
                    const healText = document.getElementById("self-heal-status-text");
                    if (healBadge) {
                        healBadge.textContent = "SAĞLIKLI";
                        healBadge.style.backgroundColor = "#10b981";
                    }
                    if (healText) {
                        healText.textContent = "Açılış denetimi ve onarım başarıyla tamamlandı. Sistem aktif.";
                    }
                    if (typeof updateSteamToolsStatus === "function") {
                        updateSteamToolsStatus();
                    }
                }, 1300);
            } else {
                btnRepair.style.background = "linear-gradient(135deg, #10b981, #059669)";
                btnRepair.style.color = "#ffffff";
                btnRepair.innerHTML = '<i class="fa-solid fa-circle-check"></i> Onarım Tamamlandı';
                setTimeout(() => {
                    modal.classList.remove("active");
                    window.removeEventListener("keydown", blockEscHandler, true);
                }, 1300);
            }
        } catch (err) {
            btnRepair.disabled = false;
            btnRepair.innerHTML = '<i class="fa-solid fa-rotate-right"></i> Tekrar Dene';
        }
    };
}

// %% Clock Initialization
function initClock() {
    const timeEl = document.getElementById("clock-time");
    const secEl = document.getElementById("clock-seconds");
    const dateEl = document.getElementById("clock-date");
    if (!timeEl || !secEl || !dateEl) return;

    const days = ["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"];
    const months = [
        "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
        "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
    ];

    function updateClock() {
        const now = new Date();
        
        // Time
        let hours = String(now.getHours()).padStart(2, '0');
        let minutes = String(now.getMinutes()).padStart(2, '0');
        timeEl.textContent = `${hours}:${minutes}`;
        
        // Seconds
        secEl.textContent = String(now.getSeconds()).padStart(2, '0');
        
        // Date
        const dayName = days[now.getDay()];
        const dayNum = now.getDate();
        const monthName = months[now.getMonth()];
        dateEl.textContent = `${dayNum} ${monthName}, ${dayName}`;
    }

    updateClock();
    setInterval(updateClock, 1000);
}

// %% Tabs Switching
let fetchDealsGlobal = null;

function initTabs() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            // Remove active classes
            tabButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            
            // Add active class
            btn.classList.add("active");
            const targetEl = document.getElementById(`tab-${targetTab}`);
            if (targetEl) targetEl.classList.add("active");

            // Diagnostic fetch on settings tab click
            if (targetTab === "settings") {
                if (typeof updateSteamToolsStatus === "function") updateSteamToolsStatus();
                if (typeof updateVCRedistStatus === "function") updateVCRedistStatus();
                if (typeof updateSecurityStatus === "function") updateSecurityStatus();
                if (typeof pollComponentUpdateStatus === "function") pollComponentUpdateStatus();
                if (typeof loadSteamLibraries === "function") loadSteamLibraries();
            }

            if (targetTab === "discount-leak" && typeof fetchDealsGlobal === "function") {
                fetchDealsGlobal();
            }

            if (targetTab === "achievements" && typeof loadSAMLibrary === "function") {
                loadSAMLibrary(samAllGames.length === 0);
            }
        });
    });
}

// %% Core Application logic
function initAppLogic() {
    const appidInput = document.getElementById("appid-input");
    const btnAddAppid = document.getElementById("btn-add-appid");
    const btnRestartSteam = document.getElementById("btn-restart-steam");
    
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");

    // Discount Leak Elements & Variables
    const dealsGrid = document.getElementById("deals-grid");
    const priceSlider = document.getElementById("price-range-slider");
    const priceDisplay = document.getElementById("price-limit-display");
    const genreBtns = document.querySelectorAll(".btn-genre");

    const discountBtns = document.querySelectorAll(".btn-discount");

    let allDeals = [];
    let activeGenre = "all";
    let maxPriceLimit = 60;
    let minDiscountLimit = "all";
    let exchangeRate = 33.0;

    fetchDealsGlobal = fetchDeals;
    
    const gamesCount = document.getElementById("games-count");
    const libraryGrid = document.getElementById("library-grid");
    const btnReloadCovers = document.getElementById("btn-reload-covers");
    const searchInput = document.getElementById("search-input");
    const sortButtons = document.querySelectorAll(".sort-btn");
    
    const pagePrev = document.getElementById("page-prev");
    const pageNext = document.getElementById("page-next");
    const pageIndicator = document.getElementById("page-indicator");
    
    const steamPathInput = document.getElementById("steam-path-input");
    const btnSavePath = document.getElementById("btn-save-path");
    const repoListContainer = document.getElementById("repo-list-container");
    
    const logTerminal = document.getElementById("log-terminal-output");
    const btnClearLogs = document.getElementById("btn-clear-log-view");
    
    const loadingOverlay = document.getElementById("loading-overlay");
    const loadingOverlayClose = document.getElementById("loading-overlay-close");
    const loadingMessage = document.getElementById("loading-message");
    const loadingProgress = document.getElementById("loading-progress");
    const loadingPercent = document.getElementById("loading-percent");

    if (loadingOverlayClose) {
        loadingOverlayClose.addEventListener("click", () => {
            if (loadingOverlay) loadingOverlay.classList.remove("active");
        });
    }

    // Window controls
    document.getElementById("close-btn").addEventListener("click", () => {
        if (window.electronAPI) {
            window.electronAPI.close();
        } else {
            fetch("/api/close", { method: "POST" }).catch(() => {});
            window.close();
        }
    });
    document.getElementById("minimize-btn").addEventListener("click", () => {
        if (window.electronAPI) {
            window.electronAPI.minimize();
        } else {
            fetch("/api/minimize", { method: "POST" }).catch(() => {});
        }
    });
    document.getElementById("maximize-btn").addEventListener("click", () => {
        if (window.electronAPI) {
            window.electronAPI.maximize();
        } else {
            fetch("/api/maximize", { method: "POST" }).catch(() => {});
        }
    });

    // Pagination & Catalog variables
    let gameLibrary = [];
    let filteredLibrary = [];
    let currentPage = 1;
    const itemsPerPage = 20;
    let currentSort = "recent"; // or "az"

    let initRetries = 0;
    const maxInitRetries = 10;

    function initApp() {
        fetch("/api/config")
            .then(res => {
                if (!res.ok) throw new Error("Backend server not ready");
                return res.json();
            })
            .then(data => {
                const statusEl = document.getElementById("status-connection");
                if (data.steam_path) {
                    steamPathInput.value = data.steam_path;
                    if (statusEl) {
                        statusEl.textContent = `Steam Bağlantısı: ${data.steam_path}`;
                        const dot = statusEl.previousElementSibling;
                        if (dot) dot.className = "status-indicator online";
                    }
                } else {
                    if (statusEl) {
                        statusEl.textContent = "Steam Bulunamadı (Settings sekmesinden yolu belirleyin)";
                        const dot = statusEl.previousElementSibling;
                        if (dot) dot.className = "status-indicator offline";
                    }
                }
                if (data.version && typeof updateVersionBadges === "function") updateVersionBadges(data.version);
                if (typeof updateSteamToolsStatus === "function") updateSteamToolsStatus();
                if (typeof updateVCRedistStatus === "function") updateVCRedistStatus();
                if (typeof updateSecurityStatus === "function") updateSecurityStatus();
                if (typeof pollComponentUpdateStatus === "function") pollComponentUpdateStatus();
                loadSteamLibraries();
                loadSettings();
                loadLibrary();

                setTimeout(() => {
                    if (typeof dismissSplashScreen === "function") dismissSplashScreen();
                }, 1200);

                // Silent background prefetch for deals (ready in memory before user clicks the tab)
                setTimeout(() => {
                    fetchDeals(false);
                }, 1200);
            })
            .catch(err => {
                console.warn("Backend not ready, retrying initial load...", err);
                if (initRetries < maxInitRetries) {
                    initRetries++;
                    setTimeout(initApp, 1000);
                } else {
                    console.error("Backend failed to respond after max retries.");
                }
            });
    }

    initApp();

    // Poll logs when log tab is visible (optional, we can do it via setinterval)
    setInterval(pollActiveLogs, 2000);

    // --- Actions ---

    // Save Steam Path
    btnSavePath.addEventListener("click", () => {
        const pathValue = steamPathInput.value.trim();
        fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ steam_path: pathValue })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert("Steam dosya yolu başarıyla kaydedildi!");
                loadSettings();
                loadLibrary();
            } else {
                alert("Hata: " + data.error);
            }
        });
    });



    // Install SteamTools
    document.getElementById("btn-install-st").addEventListener("click", () => {
        loadingMessage.textContent = "SteamTools kanca durumu kontrol ediliyor ve kuruluyor...";
        loadingOverlay.classList.add("active");
        
        fetch("/api/install_steamtools", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                loadingOverlay.classList.remove("active");
                if (data.success) {
                    if (data.already_installed) {
                        alert(data.message || "SteamTools zaten kurulu ve Steam üzerinde aktif durumda!");
                    } else {
                        alert(data.message || "SteamTools kancası başarıyla kuruldu!");
                    }
                    updateSteamToolsStatus();
                } else {
                    alert("Kurulum başarısız oldu: " + data.error);
                }
            })
            .catch(err => {
                loadingOverlay.classList.remove("active");
                alert("Ağ hatası: " + err);
            });
    });

    // Self-Healing: Sistemi Otomatik Tara ve Onar
    const btnSelfHeal = document.getElementById("btn-self-heal");
    if (btnSelfHeal) {
        btnSelfHeal.addEventListener("click", async () => {
            const healBadge = document.getElementById("self-heal-badge");
            const healText = document.getElementById("self-heal-status-text");
            
            if (healBadge) {
                healBadge.textContent = "ONARILIYOR...";
                healBadge.style.backgroundColor = "#eab308";
            }
            if (healText) {
                healText.textContent = "Sistem bileşenleri, Steam kancaları, LUA kayıtları ve önbellekler taranıyor...";
            }
            btnSelfHeal.disabled = true;

            try {
                const res = await fetch("/api/self_heal", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ force: true, restart_steam: false })
                });
                const data = await res.json();
                btnSelfHeal.disabled = false;

                if (data.ok) {
                    if (healBadge) {
                        healBadge.textContent = "SAĞLIKLI";
                        healBadge.style.backgroundColor = "#10b981";
                    }
                    const actionList = (data.actions && data.actions.length > 0)
                        ? "\n\nGerçekleştirilen İşlemler:\n• " + data.actions.join("\n• ")
                        : "";
                    if (healText) {
                        healText.textContent = `${data.actions ? data.actions.length : 0} işlem doğrulandı. Sistem tam kapasite çalışıyor.`;
                    }
                    if (typeof window.showCustomAlert === "function") {
                        await window.showCustomAlert(
                            "Kendi kendini tamir eden sistem başarıyla çalıştı!" + actionList,
                            "Otomatik Onarım Başarılı",
                            "Tamam"
                        );
                    } else {
                        alert("Otomatik Onarım Başarılı:\n" + actionList);
                    }
                    updateSteamToolsStatus();
                } else {
                    if (healBadge) {
                        healBadge.textContent = "UYARI";
                        healBadge.style.backgroundColor = "#ef4444";
                    }
                    if (healText) {
                        healText.textContent = data.error || "Onarım sırasında bir sorunla karşılaşıldı.";
                    }
                    alert("Onarım uyarısı: " + (data.error || "Bilinmeyen hata"));
                }
            } catch (err) {
                btnSelfHeal.disabled = false;
                if (healBadge) {
                    healBadge.textContent = "HATA";
                    healBadge.style.backgroundColor = "#ef4444";
                }
                alert("Bağlantı hatası: " + err);
            }
        });
    }

    // Visual C++ Runtimes (x86 & x64) Otomatik Kurulum
    const btnInstallVCRedist = document.getElementById("btn-install-vcredist");
    if (btnInstallVCRedist) {
        btnInstallVCRedist.addEventListener("click", async () => {
            const badge = document.getElementById("vcredist-status-badge");
            const statusText = document.getElementById("vcredist-status-text");

            if (badge) {
                badge.textContent = "İNDİRİLİYOR & KURULUYOR...";
                badge.style.backgroundColor = "#0284c7";
            }
            if (statusText) {
                statusText.textContent = "Microsoft resmi sunucularından Visual C++ paketleri indiriliyor ve arka planda kuruluyor...";
            }
            btnInstallVCRedist.disabled = true;

            try {
                const res = await fetch("/api/vcredist/install", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ arch: "all" })
                });
                const data = await res.json();
                btnInstallVCRedist.disabled = false;

                if (typeof updateVCRedistStatus === "function") {
                    updateVCRedistStatus();
                }

                if (data.success) {
                    if (typeof window.showCustomAlert === "function") {
                        await window.showCustomAlert(data.message, "Visual C++ Kurulumu", "Tamam");
                    } else {
                        alert(data.message);
                    }
                } else {
                    alert("Kurulum uyarısı: " + data.message);
                }
            } catch (err) {
                btnInstallVCRedist.disabled = false;
                if (typeof updateVCRedistStatus === "function") {
                    updateVCRedistStatus();
                }
                alert("Kurulum sırasında bağlantı hatası oluştu: " + err);
            }
        });
    }

    // Uninstall SteamTools
    document.getElementById("btn-uninstall-st").addEventListener("click", async () => {
        if (!await window.showCustomConfirm("SteamTools kanca (hook) DLL dosyalarını Steam'den kaldırmak istediğinize emin misiniz?")) {
            return;
        }
        
        loadingMessage.textContent = "SteamTools kanca dosyaları kaldırılıyor...";
        loadingOverlay.classList.add("active");
        
        fetch("/api/uninstall_steamtools", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                loadingOverlay.classList.remove("active");
                if (data.success) {
                    alert("SteamTools dosyaları başarıyla kaldırıldı!");
                    updateSteamToolsStatus();
                } else {
                    alert("Kaldırma başarısız oldu: " + data.error);
                }
            })
            .catch(err => {
                loadingOverlay.classList.remove("active");
                alert("Ağ hatası: " + err);
            });
    });

    // Restart Steam (from Settings box - unified with main button)
    const btnRestartST = document.getElementById("btn-restart-st");
    if (btnRestartST) {
        btnRestartST.addEventListener("click", () => {
            if (btnRestartSteam) {
                btnRestartSteam.click();
            }
        });
    }

    // Clear Steam Download Cache
    const btnClearCacheST = document.getElementById("btn-clear-cache-st");
    if (btnClearCacheST) {
        btnClearCacheST.addEventListener("click", async () => {
            if (!await window.showCustomConfirm("Steam indirme önbelleği temizlenip Steam yeniden başlatılacak. Bu işlem 'İnternet bağlantısı yok' hatalarını çözer. Devam edilsin mi?")) {
                return;
            }
            loadingMessage.textContent = "Steam indirme önbelleği temizleniyor ve Steam yeniden başlatılıyor...";
            loadingOverlay.classList.add("active");
            fetch("/api/clear_steam_cache", { method: "POST" })
                .then(res => res.json())
                .then(data => {
                    loadingOverlay.classList.remove("active");
                    if (data.success) {
                        alert(data.message || "İndirme önbelleği temizlendi ve Steam yeniden başlatıldı!");
                        setTimeout(updateSteamToolsStatus, 2000);
                    } else {
                        alert("Önbellek temizleme başarısız: " + data.error);
                    }
                })
                .catch(err => {
                    loadingOverlay.classList.remove("active");
                    alert("Hata: " + err);
                });
        });
    }

    // Nuke / Self-Destruct System
    const btnSelfDestruct = document.getElementById("btn-self-destruct");
    const nukeModal = document.getElementById("nuke-confirm-modal");
    const nukeCancel = document.getElementById("nuke-modal-cancel");
    const nukeClose = document.getElementById("nuke-modal-close");
    const nukeConfirm = document.getElementById("nuke-modal-confirm");

    if (btnSelfDestruct && nukeModal) {
        btnSelfDestruct.addEventListener("click", () => {
            nukeModal.classList.add("active");
        });

        const closeNukeModal = () => {
            nukeModal.classList.remove("active");
        };

        if (nukeCancel) nukeCancel.addEventListener("click", closeNukeModal);
        if (nukeClose) nukeClose.addEventListener("click", closeNukeModal);

        if (nukeConfirm) {
            nukeConfirm.addEventListener("click", async () => {
                closeNukeModal();
                loadingMessage.textContent = "Sistem imha ediliyor ve SteaMRogue sistemden kaldırılıyor... Lütfen bekleyin.";
                loadingOverlay.classList.add("active");

                try {
                    const res = await fetch("/api/self_destruct", { method: "POST" });
                    const data = await res.json();
                    
                    loadingMessage.textContent = "İmha işlemi tamamlandı. Uygulama kapatılıyor...";
                    
                    setTimeout(() => {
                        try {
                            if (window.electronAPI && window.electronAPI.quit) {
                                window.electronAPI.quit();
                            } else {
                                window.close();
                            }
                        } catch (e) {
                            window.close();
                        }
                    }, 1800);
                } catch (err) {
                    loadingOverlay.classList.remove("active");
                    alert("İmha işlemi sırasında bir hata oluştu: " + err);
                }
            });
        }
    }

    // Add Windows Defender exclusion
    const btnAddDefender = document.getElementById("btn-add-defender-exclusion");
    if (btnAddDefender) {
        btnAddDefender.addEventListener("click", () => {
            btnAddDefender.disabled = true;
            btnAddDefender.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Uygulanıyor...`;
            
            fetch("/api/add_exclusion", { method: "POST" })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        alert("Windows Defender dışlama komutu yönetici olarak başarıyla gönderildi!\n\nArtık Windows Defender SteaMRogue ve Steam klasörünü güvenli olarak tanıyacaktır.");
                    } else {
                        alert("Dışlama eklenirken hata oluştu: " + data.error);
                    }
                })
                .catch(err => {
                    alert("İstek gönderilemedi: " + err);
                })
                .finally(() => {
                    btnAddDefender.disabled = false;
                    btnAddDefender.innerHTML = `<i class="fa-solid fa-shield-virus"></i> Windows Defender Dışlaması Ekle`;
                });
        });
    }

    // Karantinadan Otomatik Kurtarma ve Onarım
    const btnRestoreQuarantine = document.getElementById("btn-restore-quarantine");
    if (btnRestoreQuarantine) {
        btnRestoreQuarantine.addEventListener("click", async () => {
            btnRestoreQuarantine.disabled = true;
            btnRestoreQuarantine.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Kurtarılıyor...`;

            try {
                const res = await fetch("/api/security/restore_quarantine", { method: "POST" });
                const data = await res.json();
                btnRestoreQuarantine.disabled = false;
                btnRestoreQuarantine.innerHTML = `<i class="fa-solid fa-life-ring"></i> Karantinadan Kurtar ve Onar`;

                if (typeof updateSecurityStatus === "function") {
                    updateSecurityStatus();
                }
                if (typeof updateSteamToolsStatus === "function") {
                    updateSteamToolsStatus();
                }

                if (data.success) {
                    if (typeof window.showCustomAlert === "function") {
                        await window.showCustomAlert(data.message, "Karantina Kurtarma Başarılı", "Tamam");
                    } else {
                        alert(data.message);
                    }
                } else {
                    alert("Uyarı: " + data.message);
                }
            } catch (err) {
                btnRestoreQuarantine.disabled = false;
                btnRestoreQuarantine.innerHTML = `<i class="fa-solid fa-life-ring"></i> Karantinadan Kurtar ve Onar`;
                alert("Kurtarma hatası: " + err);
            }
        });
    }

    // Harici Antivirüsler İçin İstisna Yollarını Panoya Kopyalama
    const btnCopyPaths = document.getElementById("btn-copy-exclusion-paths");
    if (btnCopyPaths) {
        btnCopyPaths.addEventListener("click", () => {
            const pathsToCopy = (typeof cachedExclusionPaths !== "undefined" && cachedExclusionPaths.length > 0)
                ? cachedExclusionPaths.join("\r\n")
                : (steamPathInput.value || "C:\\Program Files (x86)\\Steam");

            navigator.clipboard.writeText(pathsToCopy).then(() => {
                const orig = btnCopyPaths.innerHTML;
                btnCopyPaths.innerHTML = `<i class="fa-solid fa-check"></i> Kopyalandı!`;
                btnCopyPaths.style.backgroundColor = "rgba(16, 185, 129, 0.2)";
                btnCopyPaths.style.borderColor = "#10b981";
                setTimeout(() => {
                    btnCopyPaths.innerHTML = orig;
                    btnCopyPaths.style.backgroundColor = "";
                    btnCopyPaths.style.borderColor = "";
                }, 2500);
            }).catch(() => {
                prompt("Aşağıdaki klasör yollarını antivirüs istisnalarına ekleyin:", pathsToCopy);
            });
        });
    }

    // Restart Steam (Pürüzsüz Steam temalı animasyon & durum bildirimi)
    btnRestartSteam.addEventListener("click", async () => {
        if (btnRestartSteam.disabled) return;

        const originalContent = btnRestartSteam.innerHTML;
        btnRestartSteam.disabled = true;
        btnRestartSteam.classList.add("loading");
        btnRestartSteam.innerHTML = `<i class="fa-brands fa-steam fa-spin"></i> <span>Yeniden Başlatılıyor...</span>`;

        try {
            const res = await fetch("/api/restart_steam", { method: "POST" });
            const data = await res.json();
            btnRestartSteam.classList.remove("loading");
            if (data.success) {
                btnRestartSteam.classList.add("success");
                btnRestartSteam.innerHTML = `<i class="fa-solid fa-circle-check"></i> <span>Başarıyla Başlatıldı!</span>`;
                const restartBadge = document.getElementById("mode-restart-badge");
                if (restartBadge) restartBadge.style.display = "none";
            } else {
                btnRestartSteam.classList.add("error");
                btnRestartSteam.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> <span>Başarısız Oldu</span>`;
            }
        } catch (e) {
            btnRestartSteam.classList.remove("loading");
            btnRestartSteam.classList.add("error");
            btnRestartSteam.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> <span>Hata Oluştu</span>`;
        }

        setTimeout(() => {
            btnRestartSteam.classList.remove("success", "error", "loading");
            btnRestartSteam.innerHTML = originalContent;
            btnRestartSteam.disabled = false;
        }, 2600);
    });

    // %% Steam Operating Mode Switcher (Güvenli Mod vs SteaMRogue Modu)
    function initSystemMode() {
        const toggleContainer = document.getElementById("mode-toggle-pill");
        const btnSafe = document.getElementById("mode-btn-safe");
        const btnUnlocked = document.getElementById("mode-btn-unlocked");
        const restartBadge = document.getElementById("mode-restart-badge");
        const btnModeInfo = document.getElementById("btn-mode-info");
        const modeInfoModal = document.getElementById("mode-info-modal");
        const modeInfoClose = document.getElementById("mode-info-modal-close");
        const modeInfoConfirm = document.getElementById("mode-info-modal-confirm");

        if (!toggleContainer || !btnSafe || !btnUnlocked) return;

        let currentMode = "unlocked";
        let isSwitching = false;

        function updateUI(mode) {
            currentMode = mode;
            toggleContainer.setAttribute("data-active", mode);
            if (mode === "safe") {
                btnSafe.classList.add("active");
                btnUnlocked.classList.remove("active");
            } else {
                btnUnlocked.classList.add("active");
                btnSafe.classList.remove("active");
            }
            if (window.electronAPI && typeof window.electronAPI.notifyModeChanged === 'function') {
                window.electronAPI.notifyModeChanged(mode);
            }
        }

        // Listen for external mode switches from System Tray
        if (window.electronAPI && typeof window.electronAPI.onModeChanged === 'function') {
            window.electronAPI.onModeChanged((newMode) => {
                if (newMode && newMode !== currentMode) {
                    updateUI(newMode);
                }
            });
        }

        // Connect manual disclaimer review button in Settings
        const btnManualDisclaimer = document.getElementById("btn-show-disclaimer-manual");
        if (btnManualDisclaimer) {
            btnManualDisclaimer.addEventListener("click", () => {
                initDisclaimerModal(true);
            });
        }

        // Fetch initial physical disk mode from backend
        async function fetchMode() {
            try {
                const res = await fetch("/api/system/mode");
                const data = await res.json();
                if (data && data.success && data.mode) {
                    updateUI(data.mode);
                }
            } catch (err) {
                console.debug("[System Mode] Failed to fetch mode:", err);
            }
        }

        // Switch mode handler
        async function switchMode(targetMode) {
            if (isSwitching || targetMode === currentMode) return;
            isSwitching = true;

            try {
                const res = await fetch("/api/system/mode", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ mode: targetMode })
                });
                const data = await res.json();

                if (!data.success) {
                    showCustomAlert(data.error || "Mod değiştirilemedi.", "Hata");
                    return;
                }

                updateUI(targetMode);

                // Sync with Electron system tray
                try {
                    if (window.require) {
                        const { ipcRenderer } = window.require('electron');
                        ipcRenderer.send('mode-changed-in-ui', targetMode);
                    }
                } catch (e) {}

                if (targetMode === "safe") {
                    showCustomAlert(
                        "🛡️ Güvenli Mod Devreye Alındı\n\nSteamTools ve arka plan ekleme servisleri kapatıldı.\nEklediğiniz tüm oyunlar Steam kütüphanenizde eksiksiz ve oynanabilir olarak korunmaya devam ediyor.",
                        "Güvenli Mod Aktif"
                    );
                } else {
                    showCustomAlert(
                        "⚡ SteaMRogue Modu Devreye Alındı\n\nSteamTools ve kilit açıcı servisler arka planda başlatıldı.\nArtık dilediğiniz gibi yeni oyunlar ekleyebilirsiniz.",
                        "SteaMRogue Modu Aktif"
                    );
                }
            } catch (err) {
                console.error("[System Mode] Switch error:", err);
                showCustomAlert("Bağlantı hatası: Mod güncellenemedi.", "Hata");
            } finally {
                isSwitching = false;
            }
        }

        btnSafe.addEventListener("click", () => switchMode("safe"));
        btnUnlocked.addEventListener("click", () => switchMode("unlocked"));

        if (restartBadge) {
            restartBadge.addEventListener("click", () => {
                btnRestartSteam.click();
            });
        }

        // Listen for mode changes coming from Windows Tray menu
        try {
            if (window.require) {
                const { ipcRenderer } = window.require('electron');
                ipcRenderer.on('system-mode-changed', (event, newMode) => {
                    updateUI(newMode);
                });
            }
        } catch (e) {}

        // Mode Info Modal Handlers
        if (btnModeInfo && modeInfoModal) {
            btnModeInfo.addEventListener("click", () => {
                modeInfoModal.classList.add("active");
            });

            const closeInfoModal = () => modeInfoModal.classList.remove("active");
            if (modeInfoClose) modeInfoClose.addEventListener("click", closeInfoModal);
            if (modeInfoConfirm) modeInfoConfirm.addEventListener("click", closeInfoModal);
            modeInfoModal.addEventListener("click", (e) => {
                if (e.target === modeInfoModal) closeInfoModal();
            });
        }

        // Initial fetch
        fetchMode();
    }
    initSystemMode();

    // How to Use Guide Modal handlers
    const btnGuideHelp = document.getElementById("btn-guide-help");
    const guideModal = document.getElementById("guide-modal");
    const guideModalClose = document.getElementById("guide-modal-close");
    const guideModalConfirm = document.getElementById("guide-modal-confirm");

    if (btnGuideHelp && guideModal) {
        btnGuideHelp.addEventListener("click", () => {
            guideModal.classList.add("active");
        });
        if (guideModalClose) guideModalClose.addEventListener("click", () => guideModal.classList.remove("active"));
        if (guideModalConfirm) guideModalConfirm.addEventListener("click", () => guideModal.classList.remove("active"));
        guideModal.addEventListener("click", (e) => {
            if (e.target === guideModal) guideModal.classList.remove("active");
        });
    }

    // Open SteamDB (button in Discount Leak tab) → opens system browser
    const btnSteamDbLeak = document.getElementById("btn-steamdb-leak");
    if (btnSteamDbLeak) {
        btnSteamDbLeak.addEventListener("click", () => {
            if (window.electronAPI && window.electronAPI.openExternal) {
                window.electronAPI.openExternal("https://steamdb.info/sales/");
            } else {
                window.open("https://steamdb.info/sales/", "_blank");
            }
        });
    }

    // Refresh deals button in Discount Leak tab
    const btnRefreshDeals = document.getElementById("btn-refresh-deals");
    if (btnRefreshDeals) {
        btnRefreshDeals.addEventListener("click", () => {
            const icon = btnRefreshDeals.querySelector("i");
            if (icon) {
                icon.classList.add("fa-spin");
            }
            btnRefreshDeals.disabled = true;
            fetchDeals(true);
            setTimeout(() => {
                if (icon) {
                    icon.classList.remove("fa-spin");
                }
                btnRefreshDeals.disabled = false;
            }, 1000);
        });
    }

    function extractAppId(input) {
        if (!input) return "";
        const clean = String(input).trim();
        if (/^\d+$/.test(clean)) {
            return clean;
        }
        const match = clean.match(/(?:store\.steampowered\.com\/app|steamdb\.info\/app|steamcommunity\.com\/app|app)\/(\d+)/i)
                   || clean.match(/steam:\/\/store\/(\d+)/i);
        if (match && match[1]) {
            return match[1];
        }
        return clean;
    }

    // Add AppID
    btnAddAppid.addEventListener("click", async () => {
        const raw = appidInput.value.trim();
        const appid = extractAppId(raw);
        if (!appid) {
            alert("Lütfen geçerli bir Steam mağaza linki, AppID veya oyun adı girin.");
            return;
        }
        if (appid !== raw && /^\d+$/.test(appid)) {
            appidInput.value = appid;
        }

        // Show overlay
        loadingOverlay.classList.add("active");
        loadingMessage.textContent = `AppID ${appid} sorgulanıyor...`;
        loadingProgress.style.width = "0%";
        loadingPercent.textContent = "0%";

        fetch("/api/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ appid: appid })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Start polling status
                pollAddStatus(appid);
            } else {
                loadingOverlay.classList.remove("active");
                alert("Hata: " + data.error);
            }
        })
        .catch(err => {
            loadingOverlay.classList.remove("active");
            alert("Sunucuya bağlanılamadı: " + err);
        });
    });

    // Polling Status of Adding Game
    function pollAddStatus(appid) {
        let pollCount = 0;
        const pollInterval = setInterval(() => {
            pollCount++;
            fetch(`/api/add_status?appid=${appid}`)
                .then(res => res.json())
                .then(data => {
                    if (data.status === "running") {
                        loadingMessage.textContent = data.message || `AppID ${appid} işleniyor...`;
                        loadingProgress.style.width = `${Math.max(5, data.progress)}%`;
                        loadingPercent.textContent = `${data.progress}%`;
                    } else if (data.status === "success") {
                        clearInterval(pollInterval);
                        loadingOverlay.classList.remove("active");
                        appidInput.value = "";
                        loadLibrary(); // Reload list
                        const successMsg = data.message || "Oyun kütüphaneye başarıyla eklendi!";
                        showCustomConfirm(`${successMsg}\n\nSteam'in oyunu algılaması için Steam istemcisini şimdi yeniden başlatmak ister misiniz?`).then((yes) => {
                            if (yes) {
                                btnRestartSteam.click();
                            }
                        });
                    } else if (data.status === "failed") {
                        clearInterval(pollInterval);
                        loadingOverlay.classList.remove("active");
                        alert(`Oyun Eklenemedi:\n\n${data.error || "Bilinmeyen bir hata oluştu."}`);
                    } else if (data.status === "idle") {
                        // If idle after at least a few checks, the backend might have finished or aborted
                        if (pollCount > 10) {
                            clearInterval(pollInterval);
                            loadingOverlay.classList.remove("active");
                            loadLibrary();
                        }
                    }
                })
                .catch(() => {
                    clearInterval(pollInterval);
                    loadingOverlay.classList.remove("active");
                });
        }, 500);
    }

    function updateSteamToolsStatus() {
        const badge = document.getElementById("st-badge");
        const dllsList = document.getElementById("st-active-dlls");
        if (!badge || !dllsList) return;
        
        fetch("/api/bypass_status")
            .then(res => res.json())
            .then(data => {
                if (data.installed) {
                    if (data.steam_running) {
                        badge.textContent = "AKTİF (HER ŞEY YOLUNDA)";
                        badge.className = "status-badge status-active";
                        badge.style.backgroundColor = "#10b981";
                        badge.style.color = "#ffffff";
                    } else {
                        badge.textContent = "HAZIR (STEAM KAPALI)";
                        badge.className = "status-badge status-active";
                        badge.style.backgroundColor = "#2563eb";
                        badge.style.color = "#ffffff";
                    }
                    
                    if (data.dlls && data.dlls.length > 0) {
                        dllsList.textContent = data.dlls.join(", ");
                        dllsList.style.color = "#10b981";
                    } else {
                        dllsList.textContent = "Yok";
                        dllsList.style.color = "var(--text-secondary)";
                    }
                } else {
                    badge.textContent = "PASİF (KURULU DEĞİL)";
                    badge.className = "status-badge status-inactive";
                    badge.style.backgroundColor = "#8c2020";
                    badge.style.color = "#ffffff";
                    dllsList.textContent = "Yok";
                    dllsList.style.color = "var(--text-secondary)";
                }
            })
            .catch(err => {
                console.error("Error fetching bypass status:", err);
            });
    }

    function updateVCRedistStatus() {
        const badge = document.getElementById("vcredist-status-badge");
        const statusText = document.getElementById("vcredist-status-text");
        if (!badge || !statusText) return;

        fetch("/api/vcredist/status")
            .then(res => res.json())
            .then(data => {
                if (data.all_installed) {
                    badge.textContent = "KURULU (HER ŞEY YOLUNDA)";
                    badge.className = "status-badge status-active";
                    badge.style.backgroundColor = "#10b981";
                    badge.style.color = "#ffffff";
                    statusText.textContent = "Microsoft Visual C++ (x86 & x64) paketleri sisteminizde eksiksiz kurulu, her şey yolunda.";
                    statusText.style.color = "#10b981";
                } else {
                    badge.textContent = "EKSİK (YÜKLEME GEREKLİ)";
                    badge.className = "status-badge status-warning";
                    badge.style.backgroundColor = "#ef4444";
                    badge.style.color = "#ffffff";
                    statusText.textContent = data.details || "Visual C++ çalışma zamanı paketleri eksik.";
                    statusText.style.color = "#f87171";
                }
            })
            .catch(err => {
                console.error("VC++ status fetch error:", err);
            });
    }

    let cachedExclusionPaths = [];

    function updateSecurityStatus() {
        const avBadge = document.getElementById("av-detected-badge");
        const statusText = document.getElementById("av-quarantine-status-text");
        const thirdPartyTitle = document.getElementById("third-party-av-title");
        if (!avBadge || !statusText) return;

        fetch("/api/security/status")
            .then(res => res.json())
            .then(data => {
                const avInfo = data.av_info || {};
                const quarantine = data.quarantine || {};
                cachedExclusionPaths = data.exclusion_paths || [];

                const primaryAv = avInfo.primary_av || "Windows Defender";

                if (quarantine && quarantine.is_quarantined) {
                    avBadge.textContent = "UYARI (KARANTİNA)";
                    avBadge.className = "status-badge status-warning";
                    avBadge.style.backgroundColor = "#ef4444";
                    avBadge.style.color = "#ffffff";
                    statusText.textContent = `DİKKAT: ${quarantine.details || "Bazı dosyalar karantinaya alınmış olabilir."}`;
                    statusText.style.color = "#ef4444";
                } else {
                    avBadge.textContent = "GÜVENLİ (SORUN YOK)";
                    avBadge.className = "status-badge status-active";
                    avBadge.style.backgroundColor = "#10b981";
                    avBadge.style.color = "#ffffff";
                    statusText.textContent = "Kilit açıcı kütüphaneler karantinaya alınmamış, yerinde duruyor. Her şey yolunda.";
                    statusText.style.color = "#10b981";
                }

                if (avInfo.has_third_party) {
                    if (thirdPartyTitle) {
                        thirdPartyTitle.textContent = `${primaryAv} Kullandığınız Tespit Edildi:`;
                    }
                } else {
                    if (thirdPartyTitle) {
                        thirdPartyTitle.textContent = "Harici Antivirüs (Avast/Kaspersky vb.) Kullananlar İçin:";
                    }
                }
            })
            .catch(err => {
                console.error("Security status fetch error:", err);
            });
    }

    // Load Settings
    function loadSettings() {
        fetch("/api/config")
            .then(res => res.json())
            .then(data => {
                if (data.steam_path) {
                    steamPathInput.value = data.steam_path;
                    document.getElementById("status-connection").textContent = `Steam Bağlantısı: ${data.steam_path}`;
                }
                updateSteamToolsStatus();
                updateVCRedistStatus();
                updateSecurityStatus();
            });
    }

    async function loadSteamLibraries() {
        const adderSelect = document.getElementById("steam-library-select");
        const settingsSelect = document.getElementById("settings-default-library-select");
        const statusText = document.getElementById("default-library-status-text");

        try {
            const res = await fetch("/api/steam/libraries");
            const data = await res.json();
            if (data.success && data.libraries && data.libraries.length > 0) {
                const defaultLib = data.default_library || "";
                
                let optionsHtml = "";
                data.libraries.forEach(lib => {
                    const isSelected = (defaultLib && (String(lib.index) === String(defaultLib) || lib.path.toLowerCase() === defaultLib.toLowerCase())) ? "selected" : "";
                    optionsHtml += `<option value="${lib.index}" ${isSelected}>💾 ${lib.short_label}</option>`;
                });

                if (adderSelect) {
                    adderSelect.innerHTML = optionsHtml;
                }
                if (settingsSelect) {
                    settingsSelect.innerHTML = optionsHtml;
                }
                if (statusText) {
                    const activeLib = data.libraries.find(l => String(l.index) === String(defaultLib) || l.path.toLowerCase() === defaultLib.toLowerCase()) || data.libraries[0];
                    statusText.textContent = `Aktif Sürücü: ${activeLib.short_label} (${activeLib.path})`;
                    statusText.style.color = "#10b981";
                }
            } else {
                const fallbackHtml = '<option value="0">💾 Ana Steam Klasörü</option>';
                if (adderSelect) adderSelect.innerHTML = fallbackHtml;
                if (settingsSelect) settingsSelect.innerHTML = fallbackHtml;
                if (statusText) statusText.textContent = "Ek kütüphane bulunamadı, ana Steam klasörü kullanılıyor.";
            }
        } catch (err) {
            console.error("Failed loading steam libraries:", err);
            const errHtml = '<option value="0">💾 Varsayılan Kütüphane</option>';
            if (adderSelect) adderSelect.innerHTML = errHtml;
            if (settingsSelect) settingsSelect.innerHTML = errHtml;
        }
    }

    const btnSaveDefLib = document.getElementById("btn-save-default-library");
    if (btnSaveDefLib) {
        btnSaveDefLib.addEventListener("click", async () => {
            const settingsSelect = document.getElementById("settings-default-library-select");
            if (!settingsSelect) return;
            const chosenIdx = settingsSelect.value;
            btnSaveDefLib.disabled = true;
            try {
                const res = await fetch("/api/steam/set_default_library", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ library_idx: chosenIdx })
                });
                const data = await res.json();
                btnSaveDefLib.disabled = false;
                if (data.success) {
                    alert("Varsayılan kurulum sürücüsü başarıyla kaydedildi!");
                    loadSteamLibraries();
                } else {
                    alert("Hata: " + (data.error || "Kaydedilemedi"));
                }
            } catch (e) {
                btnSaveDefLib.disabled = false;
                alert("Bağlantı hatası: " + e);
            }
        });
    }

    // Helper: Identify hidden system/fix utilities (Spacewar 480, redistributables)
    function isHiddenLibraryApp(game) {
        if (!game) return true;
        const aid = String(game.appid || "").trim();
        const name = String(game.name || "").toLowerCase().trim();
        const hiddenIds = ["480", "1002", "228980", "250820", "211", "1113740", "228989", "228990"];
        if (hiddenIds.includes(aid)) return true;
        if (name.includes("spacewar") || name === "steam app 480") return true;
        return false;
    }

    // Load Library Games with instant pre-render
    function loadLibrary() {
        // 1. Instant 0ms render from localStorage cache
        try {
            const cached = localStorage.getItem("steamrogue_library_cache");
            if (cached) {
                const parsed = JSON.parse(cached);
                if (Array.isArray(parsed) && parsed.length > 0 && gameLibrary.length === 0) {
                    gameLibrary = parsed.filter(g => !isHiddenLibraryApp(g));
                    window.globalGameLibrary = gameLibrary;
                    applyFiltersAndRender();
                    renderOnlineFixLibrary();
                    if (typeof window.loadSAMLibrary === "function") {
                        try { window.loadSAMLibrary(false); } catch (e) {}
                    }
                }
            }
        } catch (e) {}

        // 2. Fast background update from server
        fetch("/api/library")
            .then(res => res.json())
            .then(data => {
                const rawGames = data.games || [];
                gameLibrary = rawGames.filter(g => !isHiddenLibraryApp(g));
                window.globalGameLibrary = gameLibrary;
                try {
                    localStorage.setItem("steamrogue_library_cache", JSON.stringify(gameLibrary));
                } catch (e) {}
                applyFiltersAndRender();
                renderOnlineFixLibrary();
                if (typeof window.loadSAMLibrary === "function") {
                    try { window.loadSAMLibrary(false); } catch (e) {}
                }
            })
            .catch(err => console.error("Failed to load library:", err));
    }

    // Refresh library button
    btnReloadCovers.addEventListener("click", () => {
        const icon = btnReloadCovers.querySelector("i");
        if (icon) {
            icon.classList.add("fa-spin");
        }
        btnReloadCovers.disabled = true;
        
        fetch("/api/library")
            .then(res => res.json())
            .then(data => {
                const rawGames = data.games || [];
                gameLibrary = rawGames.filter(g => !isHiddenLibraryApp(g));
                try {
                    localStorage.setItem("steamrogue_library_cache", JSON.stringify(gameLibrary));
                } catch (e) {}
                applyFiltersAndRender();
                renderOnlineFixLibrary();
            })
            .catch(err => {
                console.error("Failed to reload library:", err);
            })
            .finally(() => {
                setTimeout(() => {
                    if (icon) {
                        icon.classList.remove("fa-spin");
                    }
                    btnReloadCovers.disabled = false;
                }, 500);
            });
    });

    // Search and Sort inputs
    searchInput.addEventListener("input", () => {
        currentPage = 1;
        applyFiltersAndRender();
    });

    sortButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            sortButtons.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            currentSort = btn.getAttribute("data-sort");
            applyFiltersAndRender();
        });
    });

    // Pagination controls
    pagePrev.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderPage();
        }
    });

    pageNext.addEventListener("click", () => {
        const totalPages = Math.ceil(filteredLibrary.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderPage();
        }
    });

    // Apply Filter & Sort on Grid
    function applyFiltersAndRender() {
        const query = searchInput.value.toLowerCase().trim();
        
        // 1. Search Filter
        filteredLibrary = gameLibrary.filter(game => {
            if (isHiddenLibraryApp(game)) return false;
            return game.name.toLowerCase().includes(query) || String(game.appid).includes(query);
        });

        // 2. Sort
        if (currentSort === "az") {
            filteredLibrary.sort((a, b) => a.name.localeCompare(b.name));
        } else {
            // "recent" matches the default order from backend
            // No sorting needed or can sort by timestamp if added
        }

        // Update games count label
        gamesCount.textContent = `${filteredLibrary.length} oyun`;

        // Reset page if needed
        const totalPages = Math.max(1, Math.ceil(filteredLibrary.length / itemsPerPage));
        if (currentPage > totalPages) {
            currentPage = totalPages;
        }

        renderPage();
    }

    // Render current Page
    function renderPage() {
        libraryGrid.innerHTML = "";
        
        if (filteredLibrary.length === 0) {
            libraryGrid.innerHTML = `
                <div class="no-games-placeholder">
                    <i class="fa-solid fa-gamepad"></i>
                    <p>Arama kriterlerinize uygun oyun bulunamadı.</p>
                </div>`;
            pageIndicator.textContent = "Sayfa 1/1";
            pagePrev.disabled = true;
            pageNext.disabled = true;
            return;
        }

        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = Math.min(startIndex + itemsPerPage, filteredLibrary.length);
        const pageItems = filteredLibrary.slice(startIndex, endIndex);

        pageItems.forEach(game => {
            const card = document.createElement("div");
            card.className = "game-card";
            
            // Primary: Fast local NVMe/SSD high-res cover via /api/cover (serves 600x900 or vertical capsule from Steam appcache)
            const primaryCoverUrl = `/api/cover/${game.appid}`;
            const cdnFallback1 = `https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/${game.appid}/library_600x900.jpg`;
            const cdnFallback2 = `https://cdn.cloudflare.steamstatic.com/steam/apps/${game.appid}/header.jpg`;
            
            const isInst = Boolean(game.installed);
            const statusBadgeHtml = isInst 
                ? `<span style="position: absolute; top: 8px; left: 8px; background: rgba(16, 185, 129, 0.92); color: #ffffff; padding: 3px 8px; border-radius: 6px; font-size: 0.68rem; font-weight: 700; z-index: 4; display: inline-flex; align-items: center; gap: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"><i class="fa-solid fa-circle-check"></i> YÜKLÜ</span>`
                : `<span style="position: absolute; top: 8px; left: 8px; background: rgba(37, 99, 235, 0.92); color: #ffffff; padding: 3px 8px; border-radius: 6px; font-size: 0.68rem; font-weight: 700; z-index: 4; display: inline-flex; align-items: center; gap: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"><i class="fa-solid fa-download"></i> İNDİRİLEBİLİR</span>`;

            card.innerHTML = `
                <div class="card-image-wrapper">
                    ${statusBadgeHtml}
                    <img class="card-image" src="${primaryCoverUrl}" alt="${game.name}" loading="lazy" decoding="async">
                    <div class="card-overlay-actions">
                        <button class="btn-delete-card" data-appid="${game.appid}" title="Kütüphaneden Kaldır">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="game-title" title="${game.name}">${game.name}</div>
            `;

            // Handling Image Fallbacks
            const img = card.querySelector(".card-image");
            img.onerror = () => {
                if (!img.dataset.triedCdn1) {
                    img.dataset.triedCdn1 = "true";
                    img.src = cdnFallback1;
                } else if (!img.dataset.triedCdn2) {
                    img.dataset.triedCdn2 = "true";
                    img.src = cdnFallback2;
                } else {
                    // Final placeholder if all fail
                    img.style.display = "none";
                    const wrapper = card.querySelector(".card-image-wrapper");
                    if (wrapper) {
                        wrapper.innerHTML = `
                            <div class="premium-placeholder">
                                <i class="fa-solid fa-gamepad premium-placeholder-icon"></i>
                                <div class="premium-placeholder-title">${game.name}</div>
                                <div class="card-overlay-actions" style="opacity: 1;">
                                    <button class="btn-delete-card" data-appid="${game.appid}" title="Kütüphaneden Kaldır">
                                        <i class="fa-solid fa-trash"></i>
                                    </button>
                                </div>
                            </div>`;
                    }
                }
            };

            // Event listener for delete card action
            card.querySelectorAll(".btn-delete-card").forEach(delBtn => {
                delBtn.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    const appidToRemove = delBtn.getAttribute("data-appid");
                    if (await window.showCustomConfirm(`${game.name} (${appidToRemove}) kütüphanenizden kaldırılsın mı?`)) {
                        removeGame(appidToRemove);
                    }
                });
            });

            // Card click opens rich details view
            card.addEventListener("click", () => {
                openGameDetails(game.appid, game.name);
            });

            libraryGrid.appendChild(card);
        });

        // Update Pagination Indicators
        const totalPages = Math.ceil(filteredLibrary.length / itemsPerPage);
        pageIndicator.textContent = `Sayfa ${currentPage}/${totalPages}`;
        pagePrev.disabled = currentPage === 1;
        pageNext.disabled = currentPage === totalPages;
    }

    function renderOnlineFixLibrary() {
        const grid = document.getElementById("onlinefix-library-grid");
        if (!grid) return;
        grid.innerHTML = "";

        if (gameLibrary.length === 0) {
            grid.innerHTML = `
                <div class="no-games-placeholder" style="width: 100%; text-align: center; padding: 40px 0;">
                    <i class="fa-solid fa-gamepad" style="font-size: 2.2rem; color: var(--text-muted); opacity: 0.4; margin-bottom: 10px;"></i>
                    <p style="font-size: 0.85rem; color: var(--text-secondary);">Kütüphanenizde oyun bulunamadı.</p>
                </div>
            `;
            return;
        }

        gameLibrary.forEach(game => {
            const card = document.createElement("div");
            card.className = "deal-card library-fix-card";
            card.style.cursor = "pointer";
            
            const primaryCoverUrl = `/api/cover/${game.appid}?type=header`;
            const cdnFallback1 = `https://cdn.cloudflare.steamstatic.com/steam/apps/${game.appid}/header.jpg`;
            const cdnFallback2 = `https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/${game.appid}/library_600x900.jpg`;

            card.innerHTML = `
                <div class="card-image-wrapper" style="height: 120px;">
                    <img class="card-image" src="${primaryCoverUrl}" alt="${game.name}" loading="lazy" decoding="async">
                </div>
                <div class="deal-info" style="padding: 10px; text-align: center;">
                    <div class="deal-title" style="font-size: 0.82rem; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-primary);">${game.name}</div>
                    <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px;">AppID: ${game.appid}</div>
                </div>
            `;
            
            const img = card.querySelector(".card-image");
            img.onerror = () => {
                if (!img.dataset.triedCdn1) {
                    img.dataset.triedCdn1 = "true";
                    img.src = cdnFallback1;
                } else if (!img.dataset.triedCdn2) {
                    img.dataset.triedCdn2 = "true";
                    img.src = cdnFallback2;
                } else {
                    img.style.display = "none";
                    const wrapper = card.querySelector(".card-image-wrapper");
                    if (wrapper) {
                        wrapper.innerHTML = `
                            <div class="premium-placeholder" style="height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: #1a1824;">
                                <i class="fa-solid fa-gamepad" style="font-size: 1.5rem; margin-bottom: 6px; color: var(--accent-purple);"></i>
                                <div style="font-size: 0.7rem; text-align: center; padding: 0 4px; color: var(--text-secondary);">${game.name}</div>
                            </div>
                        `;
                    }
                }
            };
            
            card.addEventListener("click", () => {
                const searchInput = document.getElementById("onlinefix-search-input");
                if (searchInput) {
                    searchInput.value = game.name;
                    performOnlinefixSearch();
                    
                    const onlinefixTab = document.getElementById("tab-onlinefix");
                    if (onlinefixTab) {
                        onlinefixTab.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                }
            });
            
            grid.appendChild(card);
        });
    }

    // Remove Game API
    function removeGame(appid) {
        fetch("/api/remove", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ appid: appid })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                loadLibrary();
            } else {
                alert("Kaldırma hatası: " + data.error);
            }
        });
    }

    // Drag and Drop Zone handler
    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files);
        }
    });

    // File Upload API
    function handleFileUpload(files) {
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append("files", files[i]);
        }

        loadingOverlay.classList.add("active");
        loadingMessage.textContent = "Uploading configurations...";
        loadingProgress.style.width = "50%";
        loadingPercent.textContent = "50%";

        fetch("/api/import", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            loadingOverlay.classList.remove("active");
            if (data.success) {
                alert(`Imported: ${data.importedCount} files. Ignored: ${data.ignoredCount}.`);
                loadLibrary();
            } else {
                alert("Import failed: " + data.error);
            }
        })
        .catch(err => {
            loadingOverlay.classList.remove("active");
            alert("Upload failed: " + err);
        });
    }

    // Live Log Polling
    let lastLogLength = 0;
    function pollActiveLogs() {
        const logsTab = document.getElementById("tab-logs");
        if (!logsTab.classList.contains("active")) return;

        fetch("/api/logs")
            .then(res => res.json())
            .then(data => {
                if (data.logs) {
                    const lines = data.logs.split("\n");
                    const formatted = lines.map(line => {
                        if (line.includes("[ERROR]") || line.includes("❌") || line.includes("critical")) {
                            return `<div class="log-error">${escapeHtml(line)}</div>`;
                        } else if (line.includes("[WARNING]") || line.includes("⚠️") || line.includes("!") || line.includes("warning")) {
                            return `<div class="log-warning">${escapeHtml(line)}</div>`;
                        } else if (line.includes("[SUCCESS]") || line.includes("✅") || line.includes("OK") || line.includes("success")) {
                            return `<div class="log-success">${escapeHtml(line)}</div>`;
                        }
                        return `<div>${escapeHtml(line)}</div>`;
                    }).join("");
                    logTerminal.innerHTML = formatted;
                    logTerminal.scrollTop = logTerminal.scrollHeight;
                }
            });
    }

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Clear logs button
    btnClearLogs.addEventListener("click", () => {
        logTerminal.textContent = "";
    });

    // Autocomplete Search Dropdown
    const autocompleteBox = document.getElementById("search-autocomplete");
    let searchTimeout = null;

    appidInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            autocompleteBox.classList.remove("active");
            btnAddAppid.click();
        }
    });

    appidInput.addEventListener("paste", () => {
        setTimeout(() => {
            const rawVal = appidInput.value.trim();
            const extracted = extractAppId(rawVal);
            if (extracted && /^\d+$/.test(extracted)) {
                appidInput.value = extracted;
                appidInput.dispatchEvent(new Event("input"));
            }
        }, 40);
    });

    appidInput.addEventListener("input", () => {
        const rawValue = appidInput.value.trim();
        if (!rawValue) {
            autocompleteBox.classList.remove("active");
            return;
        }

        const value = extractAppId(rawValue);

        if (searchTimeout) clearTimeout(searchTimeout);

        searchTimeout = setTimeout(() => {
            fetch(`/api/search_store?q=${encodeURIComponent(value)}`)
                .then(res => res.json())
                .then(data => {
                    if (data.results && data.results.length > 0) {
                        autocompleteBox.innerHTML = data.results.map(item => `
                            <div class="search-item" data-id="${item.id}" data-name="${item.name}">
                                <img src="${item.tiny_image}" onerror="this.src='https://cdn.cloudflare.steamstatic.com/steam/apps/${item.id}/header.jpg'">
                                <div class="search-item-info">
                                    <div class="search-item-name">${item.name}</div>
                                    <div class="search-item-id">AppID: ${item.id}</div>
                                </div>
                            </div>
                        `).join("");
                        autocompleteBox.classList.add("active");

                        autocompleteBox.querySelectorAll(".search-item").forEach(item => {
                            item.addEventListener("click", () => {
                                appidInput.value = item.getAttribute("data-id");
                                autocompleteBox.classList.remove("active");
                            });
                        });
                    } else {
                        autocompleteBox.classList.remove("active");
                    }
                })
                .catch(() => {
                    autocompleteBox.classList.remove("active");
                });
        }, 300);
    });

    document.addEventListener("click", (e) => {
        if (!appidInput.contains(e.target) && !autocompleteBox.contains(e.target)) {
            autocompleteBox.classList.remove("active");
        }
    });

    // Game Details Modal
    const detailsModal = document.getElementById("details-modal");
    const modalClose = document.getElementById("modal-close");
    const modalBanner = document.getElementById("modal-banner");
    const modalTitle = document.getElementById("modal-title");
    const modalType = document.getElementById("modal-type");
    const modalAge = document.getElementById("modal-age");
    const modalRating = document.getElementById("modal-rating");
    const modalDescription = document.getElementById("modal-description");
    const modalBtnPlay = document.getElementById("modal-btn-play");
    const modalBtnDelete = document.getElementById("modal-btn-delete");
    const modalBtnAdd = document.getElementById("modal-btn-add");

    let activeModalAppid = null;

    function openGameDetails(appid, name) {
        activeModalAppid = appid;
        modalTitle.textContent = name;
        modalBanner.style.backgroundImage = `url('https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/header.jpg')`;
        modalType.textContent = "GAME";
        modalAge.textContent = "18+";
        modalRating.textContent = "Metacritic: --";
        modalDescription.textContent = "Loading details from Steam Store API...";
        
        // Show/hide buttons based on library membership
        const gameItem = gameLibrary.find(g => g.appid == appid);
        const isAdded = Boolean(gameItem);
        const isInstalled = gameItem ? Boolean(gameItem.installed) : false;

        if (isAdded) {
            modalBtnPlay.style.display = "";
            modalBtnDelete.style.display = "";
            modalBtnAdd.style.display = "none";
            if (isInstalled) {
                modalBtnPlay.innerHTML = '<i class="fa-solid fa-play"></i> Oyna';
                modalBtnPlay.title = "Oyunu Steam üzerinden başlat";
            } else {
                modalBtnPlay.innerHTML = '<i class="fa-solid fa-download"></i> Steam ile İndir / Yükle';
                modalBtnPlay.title = "Steam'in resmi indirme ve sürücü seçim (C/D) ekranını aç";
            }
        } else {
            modalBtnPlay.style.display = "none";
            modalBtnDelete.style.display = "none";
            modalBtnAdd.style.display = "";
        }
        
        detailsModal.classList.add("active");

        fetch(`/api/details?appid=${appid}`)
            .then(res => res.json())
            .then(data => {
                if (data.success && data.details) {
                    const details = data.details;
                    modalTitle.textContent = details.name || name;
                    modalBanner.style.backgroundImage = `url('${details.header_image || ''}')`;
                    modalType.textContent = details.type || "GAME";
                    modalAge.textContent = details.required_age ? `${details.required_age}+` : "All Ages";
                    modalRating.textContent = details.metacritic_score ? `Metacritic: ${details.metacritic_score}` : "Metacritic: --";
                    modalDescription.textContent = details.short_description || "No description available.";
                } else {
                    modalDescription.textContent = "Could not load description. Offline cache loaded.";
                }
            })
            .catch(() => {
                modalDescription.textContent = "Could not load details from Steam. Offline mode active.";
            });
    }

    modalClose.addEventListener("click", () => {
        detailsModal.classList.remove("active");
    });

    window.addEventListener("click", (e) => {
        if (e.target === detailsModal) {
            detailsModal.classList.remove("active");
        }
    });

    modalBtnPlay.addEventListener("click", () => {
        if (!activeModalAppid) return;

        fetch("/api/play", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ appid: activeModalAppid })
        })
        .then(res => res.json())
        .then(data => {
            if (!data.success) {
                alert("Başlatma başarısız: " + data.error);
            }
        });
    });

    modalBtnDelete.addEventListener("click", async () => {
        if (!activeModalAppid) return;
        if (await window.showCustomConfirm(`${activeModalAppid} AppID numaralı oyun kütüphanenizden kaldırılsın mı?`)) {
            removeGame(activeModalAppid);
            detailsModal.classList.remove("active");
        }
    });

    modalBtnAdd.addEventListener("click", () => {
        if (!activeModalAppid) return;
        detailsModal.classList.remove("active");
        installDeal(activeModalAppid, modalTitle.textContent, null);
    });

    // DISCOUNT LEAK LOGIC
    let dealsLoaded = false;  // cache flag — only fetch once unless manually refreshed
    let topDeals = [];        // Backup of original home deals

    // 0ms Instant Cache from localStorage
    try {
        const cachedDealsJson = localStorage.getItem("steamrogue_deals_cache");
        if (cachedDealsJson) {
            const parsed = JSON.parse(cachedDealsJson);
            if (Array.isArray(parsed) && parsed.length > 0) {
                topDeals = parsed;
                allDeals = parsed;
                dealsLoaded = true;
            }
        }
    } catch (e) {}

    function fetchDeals(forceRefresh = false) {
        if (dealsLoaded && !forceRefresh) {
            renderDeals();
            return;
        }

        // Only show spinner if there is no cache at all
        if (allDeals.length === 0) {
            dealsGrid.innerHTML = `
                <div class="loading-deals-spinner" style="text-align: center; padding: 50px 0; color: var(--text-secondary); width: 100%;">
                    <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2.5rem; color: var(--accent-purple); margin-bottom: 15px;"></i>
                    <p style="font-size: 0.95rem; font-weight: 600;">Steam indirimleri taranıyor...</p>
                </div>
            `;
        }
        
        const url = "/api/deals" + (forceRefresh ? "?refresh=1" : "");
        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (data.success && Array.isArray(data.deals) && data.deals.length > 0) {
                    topDeals = data.deals;
                    allDeals = data.deals;
                    exchangeRate = data.rate || exchangeRate;
                    dealsLoaded = true;
                    try {
                        localStorage.setItem("steamrogue_deals_cache", JSON.stringify(data.deals));
                    } catch (e) {}
                    renderDeals();
                } else if (allDeals.length === 0) {
                    dealsGrid.innerHTML = `
                        <div class="no-games-placeholder" style="width: 100%;">
                            <i class="fa-solid fa-triangle-exclamation" style="color: #eb5757; font-size: 2.5rem; margin-bottom: 15px;"></i>
                            <p style="font-size: 0.95rem;">İndirimler yüklenemedi: ${data.error || "Bilinmeyen hata"}</p>
                        </div>
                    `;
                }
            })
            .catch(() => {
                if (allDeals.length === 0) {
                    dealsGrid.innerHTML = `
                        <div class="no-games-placeholder" style="width: 100%;">
                            <i class="fa-solid fa-triangle-exclamation" style="color: #eb5757; font-size: 2.5rem; margin-bottom: 15px;"></i>
                            <p style="font-size: 0.95rem;">Bağlantı hatası.</p>
                        </div>
                    `;
                }
            });
    }

    function renderDeals() {
        dealsGrid.innerHTML = "";
        
        const searchInput = document.getElementById("deals-search-input");
        const query = searchInput ? searchInput.value.trim().toLowerCase() : "";
        
        // Filter deals by genre, price, minimum discount percentage, and search query
        const filtered = allDeals.filter(deal => {
            const matchesGenre = activeGenre === "all" || deal.genres.includes(activeGenre);
            const matchesPrice = deal.price_usd <= maxPriceLimit;
            const matchesDiscount = 
                minDiscountLimit === "all" ? true :
                deal.savings >= parseInt(minDiscountLimit);
            const matchesSearch = !query || deal.title.toLowerCase().includes(query);
            return matchesGenre && matchesPrice && matchesDiscount && matchesSearch;
        });
        
        if (filtered.length === 0) {
            dealsGrid.innerHTML = `
                <div class="no-games-placeholder" style="width: 100%; text-align: center; padding: 50px 0; color: var(--text-secondary);">
                    <i class="fa-solid fa-ban" style="font-size: 2.5rem; margin-bottom: 15px;"></i>
                    <p style="font-size: 0.95rem;">Filtrelere uygun oyun bulunamadı.</p>
                </div>
            `;
            return;
        }
        
        filtered.slice(0, 150).forEach(deal => {
            const card = document.createElement("div");
            card.className = "deal-card";
            
            // Ultra-lightweight capsule image (~15KB) with instant Cloudflare edge delivery
            const thumbUrl = deal.capsule_url || `https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/${deal.appid}/header.jpg`;
            const fallbackUrl = `/api/cover/${deal.appid}`;
            const isDiscounted = deal.savings > 0;
            
            card.innerHTML = `
                ${isDiscounted ? `<div class="deal-badge">-${deal.savings}%</div>` : ""}
                <div class="card-image-wrapper" style="height: 120px;">
                    <img class="card-image" src="${thumbUrl}" alt="${deal.title}" loading="lazy" decoding="async">
                </div>
                <div class="deal-info">
                    <div class="deal-title">${deal.title}</div>
                    <div class="deal-genres">
                        ${deal.genres.slice(0, 3).map(g => `<span class="deal-genre-tag">${g}</span>`).join("")}
                    </div>
                    <div class="deal-price-row">
                        ${isDiscounted ? `<span class="price-original">$${deal.normal_usd}</span>` : ""}
                        <span class="price-sale">$${deal.price_usd}</span>
                    </div>
                    <button class="btn-add-deal" data-appid="${deal.appid}" data-title="${deal.title}">
                        <i class="fa-solid fa-plus"></i> Kütüphaneye Ekle
                    </button>
                </div>
            `;
            
            // Fast fallback handling
            const img = card.querySelector(".card-image");
            img.onerror = () => {
                if (!img.dataset.triedFallback) {
                    img.dataset.triedFallback = "true";
                    img.src = fallbackUrl;
                } else {
                    img.style.display = "none";
                    const wrapper = card.querySelector(".card-image-wrapper");
                    if (wrapper) {
                        wrapper.innerHTML = `
                            <div class="premium-placeholder" style="height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; background-color: #1a1824;">
                                <i class="fa-solid fa-gamepad" style="font-size: 1.8rem; margin-bottom: 8px; color: var(--accent-purple);"></i>
                                <div style="font-size: 0.75rem; text-align: center; padding: 0 8px; color: var(--text-secondary);">${deal.title}</div>
                            </div>
                        `;
                    }
                }
            };
            
            card.style.cursor = "pointer";
            card.addEventListener("click", (e) => {
                if (e.target.closest(".btn-add-deal")) {
                    return;
                }
                openGameDetails(deal.appid, deal.title);
            });

            // Add click listener to button
            const btnAdd = card.querySelector(".btn-add-deal");
            btnAdd.addEventListener("click", () => {
                installDeal(deal.appid, deal.title, btnAdd);
            });
            
            dealsGrid.appendChild(card);
        });
    }

    function installDeal(appid, title, btnEl) {
        // Show loading overlay
        loadingOverlay.classList.add("active");
        loadingMessage.textContent = `${title} (AppID ${appid}) sorgulanıyor...`;
        loadingProgress.style.width = "0%";
        loadingPercent.textContent = "0%";
        
        fetch("/api/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ appid: appid })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                pollAddStatus(appid);
            } else {
                loadingOverlay.classList.remove("active");
                alert("Oyun Eklenemedi:\n\n" + data.error);
            }
        })
        .catch(err => {
            loadingOverlay.classList.remove("active");
            alert("Sunucuya bağlanılamadı: " + err);
        });
    }

    // Price range slider input
    priceSlider.addEventListener("input", (e) => {
        const val = parseFloat(e.target.value);
        priceDisplay.textContent = `$${val.toFixed(2)}`;
        maxPriceLimit = val;
    });

    priceSlider.addEventListener("change", () => {
        renderDeals();
    });

    // Deals search input filtering with debounce and global API fallback
    const dealsSearchInput = document.getElementById("deals-search-input");
    const btnClearDealsSearch = document.getElementById("btn-clear-deals-search");
    let dealsSearchTimeout = null;

    function fetchDealsSearch(query) {
        dealsGrid.innerHTML = `
            <div class="loading-deals-spinner" style="text-align: center; padding: 50px 0; color: var(--text-secondary); width: 100%;">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2.5rem; color: var(--accent-color); margin-bottom: 15px;"></i>
                <p style="font-size: 0.95rem; font-weight: 600;">Steam indirimleri taranıyor...</p>
            </div>
        `;
        fetch(`/api/deals?title=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    allDeals = data.deals;
                    exchangeRate = data.rate;
                    renderDeals();
                } else {
                    dealsGrid.innerHTML = `
                        <div class="no-games-placeholder" style="width: 100%;">
                            <i class="fa-solid fa-triangle-exclamation" style="color: #eb5757; font-size: 2.5rem; margin-bottom: 15px;"></i>
                            <p style="font-size: 0.95rem;">Arama başarısız: ${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(() => {
                dealsGrid.innerHTML = `
                    <div class="no-games-placeholder" style="width: 100%;">
                        <i class="fa-solid fa-triangle-exclamation" style="color: #eb5757; font-size: 2.5rem; margin-bottom: 15px;"></i>
                        <p style="font-size: 0.95rem;">Bağlantı hatası.</p>
                    </div>
                `;
            });
    }

    if (dealsSearchInput) {
        dealsSearchInput.addEventListener("input", () => {
            const query = dealsSearchInput.value.trim();
            if (btnClearDealsSearch) {
                btnClearDealsSearch.style.display = query ? "inline-block" : "none";
            }
            
            clearTimeout(dealsSearchTimeout);
            dealsSearchTimeout = setTimeout(() => {
                if (query.length >= 2) {
                    fetchDealsSearch(query);
                } else if (query.length === 0) {
                    allDeals = topDeals;
                    renderDeals();
                }
            }, 450);
        });
    }

    if (btnClearDealsSearch) {
        btnClearDealsSearch.addEventListener("click", () => {
            dealsSearchInput.value = "";
            btnClearDealsSearch.style.display = "none";
            allDeals = topDeals;
            renderDeals();
        });
    }

    // Genre buttons toggling
    genreBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            genreBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeGenre = btn.getAttribute("data-genre");
            renderDeals();
        });
    });

    // Discount percentage buttons toggling
    discountBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            discountBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            minDiscountLimit = btn.getAttribute("data-min-discount");
            renderDeals();
        });
    });

    // --- OnlineFix Section Logic ---
    const onlinefixSearchInput = document.getElementById("onlinefix-search-input");
    const btnOnlinefixSearch = document.getElementById("btn-onlinefix-search");
    const onlinefixResultsGrid = document.getElementById("onlinefix-results-grid");
    const onlinefixDownloadPanel = document.getElementById("onlinefix-download-panel");
    const onlinefixDlFilename = document.getElementById("onlinefix-dl-filename");
    const onlinefixDlSpeed = document.getElementById("onlinefix-dl-speed");
    const onlinefixDlProgressBar = document.getElementById("onlinefix-dl-progress-bar");
    const onlinefixDlStatus = document.getElementById("onlinefix-dl-status");
    const onlinefixDlPercent = document.getElementById("onlinefix-dl-percent");
    const onlinefixDlCancel = document.getElementById("onlinefix-dl-cancel");
    const onlinefixDlOpen = document.getElementById("onlinefix-dl-open");
    const rarPwEl = document.getElementById("onlinefix-rar-pw");
    const btnCopyRarPw = document.getElementById("btn-copy-rar-pw");

    let currentDlTaskId = null;
    let onlinefixPollInterval = null;

    if (btnOnlinefixSearch) {
        btnOnlinefixSearch.addEventListener("click", performOnlinefixSearch);
    }
    if (onlinefixSearchInput) {
        onlinefixSearchInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") performOnlinefixSearch();
        });
    }

    if (onlinefixDlCancel) {
        onlinefixDlCancel.addEventListener("click", cancelOnlinefixDownload);
    }

    let lastDlTaskId = null;
    if (onlinefixDlOpen) {
        onlinefixDlOpen.addEventListener("click", () => {
            try {
                navigator.clipboard.writeText("online-fix.me");
            } catch (e) {}

            fetch("/api/onlinefix/open_desktop", { 
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ task_id: currentDlTaskId || lastDlTaskId })
            })
            .catch(err => console.error("Error opening archive:", err));
        });
    }

    function copyRarPassword() {
        navigator.clipboard.writeText("online-fix.me")
            .then(() => {
                if (btnCopyRarPw) {
                    const originalColor = btnCopyRarPw.style.color;
                    btnCopyRarPw.style.color = "#10b981";
                    btnCopyRarPw.className = "fa-solid fa-check";
                    setTimeout(() => {
                        btnCopyRarPw.style.color = originalColor;
                        btnCopyRarPw.className = "fa-regular fa-copy";
                    }, 2000);
                }
            })
            .catch(err => console.error("Password copy failed:", err));
    }

    if (rarPwEl) rarPwEl.addEventListener("click", copyRarPassword);
    if (btnCopyRarPw) btnCopyRarPw.addEventListener("click", copyRarPassword);

    function performOnlinefixSearch() {
        const query = onlinefixSearchInput.value.trim();
        if (!query) {
            alert("Lütfen aramak istediğiniz oyunun adını girin.");
            return;
        }

        // Disable search controls
        if (btnOnlinefixSearch) {
            btnOnlinefixSearch.disabled = true;
            btnOnlinefixSearch.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Aranıyor...`;
        }
        if (onlinefixSearchInput) onlinefixSearchInput.disabled = true;

        onlinefixResultsGrid.innerHTML = `
            <div class="loading-deals-spinner" style="text-align: center; padding: 50px 0; color: var(--text-secondary); width: 100%;">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2.5rem; color: var(--accent-color); margin-bottom: 15px;"></i>
                <p style="font-size: 0.95rem; font-weight: 600;">Online-fix.me üzerinde multiplayer yamalar aranıyor...</p>
            </div>
        `;

        fetch(`/api/onlinefix/search?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    renderOnlinefixResults(data.results);
                } else {
                    onlinefixResultsGrid.innerHTML = `
                        <div class="no-games-placeholder" style="width: 100%;">
                            <i class="fa-solid fa-triangle-exclamation" style="color: #eb5757; font-size: 2.5rem; margin-bottom: 15px;"></i>
                            <p style="font-size: 0.95rem;">Arama başarısız: ${data.error}</p>
                        </div>
                    `;
                }
            })
            .catch(err => {
                onlinefixResultsGrid.innerHTML = `
                    <div class="no-games-placeholder" style="width: 100%;">
                        <i class="fa-solid fa-triangle-exclamation" style="color: #eb5757; font-size: 2.5rem; margin-bottom: 15px;"></i>
                        <p style="font-size: 0.95rem;">Bağlantı hatası. Arka plan sunucusunun çalıştığından emin olun.</p>
                    </div>
                `;
            })
            .finally(() => {
                // Re-enable search controls
                if (btnOnlinefixSearch) {
                    btnOnlinefixSearch.disabled = false;
                    btnOnlinefixSearch.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> Ara`;
                }
                if (onlinefixSearchInput) onlinefixSearchInput.disabled = false;
            });
    }

    let selectedOnlinefixUrl = null;
    let selectedOnlinefixAppid = null;
    let currentDlMode = "desktop";

    // Setup OnlineFix Choice Modal Event Listeners
    const onlinefixChoiceModal = document.getElementById("onlinefix-choice-modal");
    const onlinefixChoiceClose = document.getElementById("onlinefix-choice-close");
    const onlinefixChoiceCancel = document.getElementById("onlinefix-choice-cancel");
    const btnChoiceDesktop = document.getElementById("btn-choice-desktop");
    const btnChoiceIntegrate = document.getElementById("btn-choice-integrate");

    if (onlinefixChoiceClose) {
        onlinefixChoiceClose.addEventListener("click", () => {
            onlinefixChoiceModal.classList.remove("active");
        });
    }
    if (onlinefixChoiceCancel) {
        onlinefixChoiceCancel.addEventListener("click", () => {
            onlinefixChoiceModal.classList.remove("active");
        });
    }
    if (btnChoiceDesktop) {
        btnChoiceDesktop.addEventListener("click", () => {
            if (onlinefixChoiceModal) onlinefixChoiceModal.classList.remove("active");
            triggerOnlinefixDownload("desktop");
        });
    }
    if (btnChoiceIntegrate) {
        btnChoiceIntegrate.addEventListener("click", () => {
            if (onlinefixChoiceModal) onlinefixChoiceModal.classList.remove("active");
            triggerOnlinefixDownload("integrate");
        });
    }

    function openInDefaultBrowser(url) {
        if (!url) return;
        if (window.electronAPI && typeof window.electronAPI.openExternal === 'function') {
            window.electronAPI.openExternal(url);
        } else {
            fetch("/api/open_browser", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: url })
            }).catch(() => {
                window.open(url, "_blank");
            });
        }
    }

    function renderOnlinefixResults(results) {
        onlinefixResultsGrid.innerHTML = "";

        if (!results || results.length === 0) {
            onlinefixResultsGrid.innerHTML = `
                <div class="no-games-placeholder" style="width: 100%; text-align: center; padding: 40px 15px; color: var(--text-secondary); background: rgba(255, 255, 255, 0.02); border-radius: 12px; border: 1px dashed var(--border-color);">
                    <i class="fa-solid fa-magnifying-glass" style="font-size: 2.2rem; margin-bottom: 12px; color: var(--accent-purple);"></i>
                    <p style="font-size: 1.05rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px;">Bu oyun için Online-Fix yaması bulunamadı.</p>
                    <p style="font-size: 0.85rem; color: var(--text-muted); max-width: 480px; margin: 0 auto;">Oyunun İngilizce adını tam yazarak veya arama terimini sadeleştirerek tekrar arayabilirsiniz.</p>
                </div>
            `;
            return;
        }

        results.forEach(item => {
            const card = document.createElement("div");
            card.className = "onlinefix-card";

            // Check if game exists in local library to associate AppID
            const matchedGame = gameLibrary.find(g => {
                const titleLower = item.title.toLowerCase();
                const nameLower = g.name.toLowerCase();
                return titleLower.includes(nameLower) || nameLower.includes(titleLower);
            });
            const appid = matchedGame ? matchedGame.appid : "";

            card.innerHTML = `
                <div class="onlinefix-card-header">
                    <div class="onlinefix-badge">
                        <i class="fa-solid fa-gamepad"></i> Multiplayer Fix
                    </div>
                    <span class="onlinefix-source-tag"><i class="fa-solid fa-shield-halved"></i> Online-Fix</span>
                </div>
                <div class="onlinefix-card-body">
                    <h3 class="onlinefix-card-title" title="${item.title}">${item.title}</h3>
                    <p class="onlinefix-card-desc">Gofile sunucusu üzerinden doğrudan indirme ve Steam otomatik entegrasyonu.</p>
                </div>
                <div class="onlinefix-card-actions">
                    <button class="btn-onlinefix-download" data-url="${item.url}" data-appid="${appid}">
                        <i class="fa-solid fa-download"></i>
                        <span>Fix İndir</span>
                    </button>
                    <button class="btn-onlinefix-browser" title="Varsayılan tarayıcınızda resmi sayfayı açın">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        <span>Siteye Git</span>
                    </button>
                </div>
            `;

            const btnDl = card.querySelector(".btn-onlinefix-download");
            btnDl.addEventListener("click", () => {
                startOnlinefixDownload(item.url, appid);
            });

            const btnBrowser = card.querySelector(".btn-onlinefix-browser");
            btnBrowser.addEventListener("click", (e) => {
                e.preventDefault();
                e.stopPropagation();
                openInDefaultBrowser(item.url);
            });

            onlinefixResultsGrid.appendChild(card);
        });
    }

    function startOnlinefixDownload(detailUrl, appid) {
        if (currentDlTaskId) {
            alert("Aynı anda sadece bir dosya indirebilirsiniz. Lütfen mevcut indirmeyi bekleyin.");
            return;
        }

        selectedOnlinefixUrl = detailUrl;
        selectedOnlinefixAppid = appid;

        if (onlinefixChoiceModal) {
            if (btnChoiceIntegrate) {
                if (appid) {
                    btnChoiceIntegrate.disabled = false;
                    btnChoiceIntegrate.style.opacity = "1";
                    btnChoiceIntegrate.style.cursor = "pointer";
                } else {
                    btnChoiceIntegrate.disabled = true;
                    btnChoiceIntegrate.style.opacity = "0.5";
                    btnChoiceIntegrate.style.cursor = "not-allowed";
                }
            }
            onlinefixChoiceModal.classList.add("active");
        } else {
            // Fallback if modal elements not loaded
            triggerOnlinefixDownload("desktop");
        }
    }

    function triggerOnlinefixDownload(mode) {
        currentDlMode = mode;

        // Show panel & reset buttons
        onlinefixDownloadPanel.style.display = "flex";
        if (onlinefixDlCancel) onlinefixDlCancel.style.display = "inline-block";
        if (onlinefixDlOpen) onlinefixDlOpen.style.display = "none";
        
        onlinefixDlFilename.textContent = "Dosya: Bağlantılar çözümleniyor...";
        onlinefixDlSpeed.textContent = "0.00 KB/s";
        onlinefixDlProgressBar.style.width = "0%";
        onlinefixDlStatus.textContent = mode === "integrate" ? "Yamayı indirip oyuna otomatik entegre etmek için başlatılıyor..." : "Masaüstüne indirme görevi sunucudan talep ediliyor...";
        onlinefixDlPercent.textContent = "0%";

        fetch("/api/onlinefix/download", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                url: selectedOnlinefixUrl,
                mode: mode,
                appid: selectedOnlinefixAppid
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                currentDlTaskId = data.task_id;
                pollOnlinefixDownloadProgress();
            } else {
                onlinefixDownloadPanel.style.display = "none";
                alert("İndirme başlatılamadı: " + data.error);
            }
        })
        .catch(err => {
            onlinefixDownloadPanel.style.display = "none";
            alert("Sunucuya bağlanılamadı: " + err);
        });
    }

    async function cancelOnlinefixDownload() {
        if (!currentDlTaskId) return;

        const wantCancel = await showCustomConfirm("İndirme işlemini iptal etmek istediğinize emin misiniz?", "İndirmeyi İptal Et", "Evet, İptal Et", "Devam Et");
        if (wantCancel) {
            fetch("/api/onlinefix/cancel", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ task_id: currentDlTaskId })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    clearInterval(onlinefixPollInterval);
                    onlinefixDlStatus.textContent = "İndirme kullanıcı tarafından iptal edildi.";
                    onlinefixDlSpeed.textContent = "İptal edildi";
                    if (onlinefixDlCancel) onlinefixDlCancel.style.display = "none";
                    currentDlTaskId = null;
                    setTimeout(() => {
                        if (!currentDlTaskId) onlinefixDownloadPanel.style.display = "none";
                    }, 4000);
                }
            })
            .catch(err => {
                console.error("Cancellation error:", err);
            });
        }
    }

    function pollOnlinefixDownloadProgress() {
        if (onlinefixPollInterval) clearInterval(onlinefixPollInterval);

        onlinefixPollInterval = setInterval(() => {
            if (!currentDlTaskId) {
                clearInterval(onlinefixPollInterval);
                return;
            }

            fetch(`/api/onlinefix/status?task_id=${currentDlTaskId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.status === "running") {
                        if (data.file_name) {
                            onlinefixDlFilename.textContent = "Dosya: " + data.file_name;
                        } else {
                            onlinefixDlFilename.textContent = "Dosya: Bağlantılar çözümleniyor...";
                        }
                        
                        onlinefixDlSpeed.textContent = data.speed || "0.00 KB/s";
                        onlinefixDlProgressBar.style.width = `${Math.max(2, data.progress)}%`;
                        onlinefixDlStatus.textContent = data.message || "Yama indiriliyor...";
                        onlinefixDlPercent.textContent = `${data.progress}%`;
                    } else if (data.status === "success") {
                        clearInterval(onlinefixPollInterval);
                        onlinefixDlProgressBar.style.width = "100%";
                        onlinefixDlPercent.textContent = "100%";
                        onlinefixDlStatus.textContent = data.message || "İndirme tamamlandı!";
                        onlinefixDlSpeed.textContent = "Tamamlandı";
                        
                        // Hide cancel, show open desktop button if in desktop mode
                        if (onlinefixDlCancel) onlinefixDlCancel.style.display = "none";
                        
                        if (currentDlMode === "desktop") {
                            if (onlinefixDlOpen) onlinefixDlOpen.style.display = "inline-block";
                            alert("Multiplayer yaması başarıyla Masaüstünüze indirildi!");
                        } else {
                            alert("Multiplayer yama dosyaları oyuna başarıyla entegre edildi!");
                        }
                        lastDlTaskId = currentDlTaskId;
                        currentDlTaskId = null;
                    } else if (data.status === "failed") {
                        clearInterval(onlinefixPollInterval);
                        onlinefixDlStatus.textContent = data.message || "İndirme tamamlanamadı.";
                        onlinefixDlSpeed.textContent = "Hata";
                        if (onlinefixDlCancel) onlinefixDlCancel.style.display = "none";
                        
                        let extraNote = "";
                        const targetUrl = data.gofile_url || data.detail_url;
                        if (targetUrl) {
                            extraNote = "\n\nİsterseniz indirme sayfasını tarayıcınızda açıp doğrudan oradan da indirebilirsiniz.";
                        }
                        alert("Yama İndirilemedi:\n\n" + data.message + extraNote);
                        
                        if (targetUrl && onlinefixDlOpen) {
                            onlinefixDlOpen.style.display = "inline-block";
                            onlinefixDlOpen.innerHTML = `<i class="fa-solid fa-globe"></i> Sayfayı Tarayıcıda Aç`;
                            onlinefixDlOpen.onclick = () => {
                                openInDefaultBrowser(targetUrl);
                            };
                        }

                        currentDlTaskId = null;
                        setTimeout(() => {
                            if (!currentDlTaskId && (!targetUrl || onlinefixDlOpen.style.display === "none")) {
                                onlinefixDownloadPanel.style.display = "none";
                            }
                        }, 10000);
                    }
                })
                .catch(() => {
                    clearInterval(onlinefixPollInterval);
                    onlinefixDownloadPanel.style.display = "none";
                    currentDlTaskId = null;
                });
        }, 1000);
    }
}

// Auto-Updater In-App Notification Card Handler
if (window.electronAPI && typeof window.electronAPI.onUpdaterStatus === 'function') {
    const banner = document.getElementById("updater-banner");
    const title = document.getElementById("updater-title");
    const desc = document.getElementById("updater-desc");
    const badge = document.getElementById("updater-version-badge");
    const iconWrapper = document.getElementById("updater-icon-wrapper");
    const icon = document.getElementById("updater-icon");
    const progContainer = document.getElementById("updater-progress-container");
    const progBar = document.getElementById("updater-progress-bar");
    const progPercent = document.getElementById("updater-progress-percent");
    const progLabel = document.getElementById("updater-progress-label");
    const actions = document.getElementById("updater-actions");
    const btnRestart = document.getElementById("btn-updater-restart");
    const btnLater = document.getElementById("btn-updater-later");
    const btnClose = document.getElementById("btn-updater-close");

    const btnCheckUpdate = document.getElementById("btn-check-app-update");
    const btnRepairUpdate = document.getElementById("btn-repair-app-update");
    const updateStatusText = document.getElementById("app-update-status-text");

    // Dynamic app version initialization from Electron core
    if (typeof window.electronAPI.getAppVersion === 'function') {
        window.electronAPI.getAppVersion().then(ver => {
            if (ver) {
                const topBadge = document.getElementById("app-version-badge");
                if (topBadge) topBadge.textContent = `v${ver}`;
                const settingsBadge = document.getElementById("settings-app-version-badge");
                if (settingsBadge) settingsBadge.textContent = `v${ver}`;
            }
        }).catch(console.error);
    }

    let isManualCheck = false;

    if (btnCheckUpdate) {
        btnCheckUpdate.addEventListener("click", () => {
            isManualCheck = true;
            btnCheckUpdate.disabled = true;
            btnCheckUpdate.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Denetleniyor...';
            if (updateStatusText) {
                updateStatusText.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="color: var(--accent-purple);"></i> GitHub üzerinden yeni sürüm kontrolü yapılıyor...';
                updateStatusText.style.color = "var(--text-secondary)";
            }
            if (window.electronAPI.checkForUpdates) {
                window.electronAPI.checkForUpdates();
            }
            setTimeout(() => {
                if (btnCheckUpdate.disabled) {
                    btnCheckUpdate.disabled = false;
                    btnCheckUpdate.innerHTML = '<i class="fa-solid fa-cloud-arrow-down"></i> Güncellemeleri Denetle';
                }
            }, 6000);
        });
    }

    let isHotfixAction = false;

    if (btnRepairUpdate) {
        btnRepairUpdate.addEventListener("click", async () => {
            const confirmRepair = await showCustomConfirm(
                "SteaMRogue'un en son sürümü GitHub üzerinden temiz olarak indirilip kurulacak.\n\nBu işlem mevcut dosyalarınızı onarır ve en güncel sürüme yükseltir. Devam etmek istiyor musunuz?",
                "Sürümü Onar & Yeniden Yükle",
                "Evet, İndir ve Kur",
                "İptal"
            );
            if (confirmRepair) {
                btnRepairUpdate.disabled = true;
                btnRepairUpdate.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İndiriliyor...';
                if (updateStatusText) {
                    updateStatusText.innerHTML = '<i class="fa-solid fa-cloud-arrow-down fa-bounce" style="color: #3b82f6;"></i> En güncel kurulum paketi indiriliyor...';
                    updateStatusText.style.color = "#3b82f6";
                }
                if (window.electronAPI.repairAndReinstall) {
                    window.electronAPI.repairAndReinstall();
                }
            }
        });
    }

    // Component, Manifest & Signature Live Synchronizer
    const btnCheckComponents = document.getElementById("btn-check-components");
    const compBadge = document.getElementById("components-status-badge");
    const compStatusText = document.getElementById("components-update-status-text");
    const compStStatus = document.getElementById("comp-st-status");
    const compSigStatus = document.getElementById("comp-sig-status");
    const compRepoStatus = document.getElementById("comp-repo-status");
    const compBypassStatus = document.getElementById("comp-bypass-status");

    let componentPollTimer = null;

    async function pollComponentUpdateStatus() {
        if (componentPollTimer) {
            clearTimeout(componentPollTimer);
            componentPollTimer = null;
        }

        try {
            const res = await fetch("/api/component_update_status");
            if (!res.ok) return;
            const data = await res.json();
            if (data) {
                if (compBadge) {
                    compBadge.textContent = data.running ? "EŞİTLENİYOR..." : "GÜNCEL";
                    compBadge.style.backgroundColor = data.running ? "#eab308" : "#10b981";
                }
                if (compStatusText) {
                    if (data.running) {
                        compStatusText.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="color: #38bdf8;"></i> Harici depolar, imzalar ve oyun manifestoları arka planda senkronize ediliyor...';
                        compStatusText.style.color = "#facc15";
                    } else if (data.last_run_formatted) {
                        compStatusText.textContent = `Son Senkronizasyon: ${data.last_run_formatted} (Tüm bileşenler ve kaynaklar aktif)`;
                        compStatusText.style.color = "#10b981";
                    } else {
                        compStatusText.textContent = "Tüm depolar, kancalar ve manifest kaynakları aktif.";
                        compStatusText.style.color = "#10b981";
                    }
                }
                if (compStStatus) {
                    compStStatus.textContent = (data.steamtools && data.steamtools.updated) ? "Yeni Güncellendi" : "Eşitlendi (Aktif)";
                    compStStatus.style.color = "#4ade80";
                }
                if (compSigStatus) {
                    compSigStatus.textContent = "Dinamik Uyumlu";
                    compSigStatus.style.color = "#4ade80";
                }
                if (compRepoStatus) {
                    const repoCount = (data.repos && Object.keys(data.repos).length) || 4;
                    compRepoStatus.textContent = `${repoCount}/${repoCount} Aktif`;
                    compRepoStatus.style.color = "#4ade80";
                }
                if (compBypassStatus) {
                    compBypassStatus.textContent = "Çevrimiçi Eşit";
                    compBypassStatus.style.color = "#4ade80";
                }

                // If sync is running in the background, poll again after 1 second!
                if (data.running) {
                    componentPollTimer = setTimeout(pollComponentUpdateStatus, 1000);
                }
            }
        } catch (e) {
            console.debug("[Component Status Poll]", e);
        }
    }

    window.pollComponentUpdateStatus = pollComponentUpdateStatus;

    if (btnCheckComponents) {
        btnCheckComponents.addEventListener("click", async () => {
            btnCheckComponents.disabled = true;
            btnCheckComponents.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Eşitleniyor...';
            if (compBadge) {
                compBadge.textContent = "EŞİTLENİYOR...";
                compBadge.style.backgroundColor = "#eab308";
            }
            if (compStatusText) {
                compStatusText.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="color: #38bdf8;"></i> Manifest depoları, SteamTools DLL, TOML imzaları ve OnlineFix verileri taranıyor...';
            }

            try {
                const res = await fetch("/api/check_components_now", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ force: true })
                });
                const data = await res.json();

                if (compBadge) {
                    compBadge.textContent = "GÜNCEL";
                    compBadge.style.backgroundColor = "#10b981";
                }
                if (compStStatus) compStStatus.textContent = "Doğrulandı";
                if (compSigStatus) compSigStatus.textContent = "Steam ile Uyumlu";
                if (compRepoStatus) compRepoStatus.textContent = "4/4 Güncel";
                if (compBypassStatus) compBypassStatus.textContent = "Çevrimiçi Eşit";

                const nowStr = new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                if (compStatusText) {
                    compStatusText.textContent = `Son Senkronizasyon: Bugün ${nowStr} (Tam başarıyla tamamlandı)`;
                }

                let actionsList = "";
                if (data && Array.isArray(data.actions) && data.actions.length > 0) {
                    actionsList = "\n\nUygulanan Güncellemeler:\n• " + data.actions.join("\n• ");
                } else {
                    actionsList = "\n\nTüm manifest depoları, SteamTools kilit açıcıları ve imza motoru zaten en güncel durumdaydı.";
                }

                await window.showCustomAlert(
                    `Bileşen, Manifest ve İmza senkronizasyonu tamamlandı!${actionsList}`,
                    "Senkronizasyon Başarılı"
                );
            } catch (err) {
                if (compBadge) {
                    compBadge.textContent = "HATA";
                    compBadge.style.backgroundColor = "#ef4444";
                }
                if (compStatusText) {
                    compStatusText.textContent = `Senkronizasyon sırasında hata oluştu: ${err.message || err}`;
                }
                await window.showCustomAlert(
                    `Bileşenler eşitlenirken bir hata oluştu:\n${err.message || err}`,
                    "Senkronizasyon Hatası"
                );
            } finally {
                btnCheckComponents.disabled = false;
                btnCheckComponents.innerHTML = '<i class="fa-solid fa-arrows-rotate"></i> Bileşenleri & İmzaları Şimdi Güncelle';
            }
        });
    }

    setTimeout(pollComponentUpdateStatus, 1500);


    if (btnClose) {
        btnClose.addEventListener("click", () => {
            if (banner) banner.style.display = "none";
        });
    }

    if (btnLater) {
        btnLater.addEventListener("click", () => {
            if (banner) banner.style.display = "none";
        });
    }

    window.electronAPI.onUpdaterStatus((data) => {
        if (!data) return;

        if (btnCheckUpdate) {
            btnCheckUpdate.disabled = false;
            btnCheckUpdate.innerHTML = '<i class="fa-solid fa-cloud-arrow-down"></i> Güncellemeleri Denetle';
        }

        if (btnRepairUpdate && data.status !== "downloading") {
            btnRepairUpdate.disabled = false;
            btnRepairUpdate.innerHTML = '<i class="fa-solid fa-wrench"></i> Son Sürümü Yeniden İndir / Onar';
        }

        if (data.status === "checking") {
            if (updateStatusText) {
                updateStatusText.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin" style="color: #7c3aed;"></i> Güncellemeler denetleniyor...';
                updateStatusText.style.color = "var(--text-secondary)";
            }
        } else if (data.status === "not-available") {
            const ver = data.version ? `v${data.version}` : 'v1.1.9';
            if (updateStatusText) {
                updateStatusText.innerHTML = `<i class="fa-solid fa-circle-check" style="color: #10b981;"></i> Harika! Zaten en güncel sürümü (${ver}) kullanıyorsunuz.`;
                updateStatusText.style.color = "#10b981";
            }
            if (isManualCheck) {
                showCustomAlert(`Şu anda en son sürümü (${ver}) kullanıyorsunuz. Yeni bir güncelleme bulunmuyor.`, "SteaMRogue Güncel");
                isManualCheck = false;
            }
        } else if (data.status === "hotfix-available") {
            const ver = data.version ? `v${data.version}` : 'v1.1.9';
            isHotfixAction = true;
            if (updateStatusText) {
                updateStatusText.innerHTML = `<i class="fa-solid fa-sparkles" style="color: #a78bfa;"></i> GitHub'da güncellenmiş yeni bir paket (${ver}) yayınlandı!`;
                updateStatusText.style.color = "#a78bfa";
            }
            if (banner) {
                banner.style.display = "block";
                if (progContainer) progContainer.style.display = "none";
                if (title) title.textContent = "Yeni Güncelleme Mevcut!";
                if (badge) {
                    badge.textContent = ver;
                    badge.style.display = "inline-block";
                }
                if (desc) desc.textContent = `GitHub üzerinde ${ver} sürümü için güncellenmiş yeni bir kurulum paketi yayınlandı.`;
                if (actions) {
                    actions.style.display = "flex";
                    btnRestart.innerHTML = '<i class="fa-solid fa-cloud-arrow-down"></i> Şimdi İndir & Kur';
                    btnRestart.disabled = false;
                }
                if (icon) icon.className = "fa-solid fa-sparkles";
                if (iconWrapper) iconWrapper.className = "update-icon-wrapper";
            }
            if (isManualCheck) {
                isManualCheck = false;
                showCustomConfirm(
                    `GitHub üzerinde ${ver} sürümü için güncellenmiş yeni bir paket yayınlandı.\n\nŞimdi indirilip kurulsun mu?`,
                    "Güncelleme Paketi Mevcut",
                    "Şimdi İndir ve Kur",
                    "Daha Sonra"
                ).then((wantHotfix) => {
                    if (wantHotfix && window.electronAPI.repairAndReinstall) {
                        window.electronAPI.repairAndReinstall();
                    }
                });
            }
        } else if (data.status === "dev-mode") {
            if (updateStatusText) {
                updateStatusText.innerHTML = '<i class="fa-solid fa-code" style="color: #f59e0b;"></i> Geliştirici modu: Canlı repo takibindedir (kurulu sürümde aktiftir).';
                updateStatusText.style.color = "#f59e0b";
            }
            if (isManualCheck) {
                showCustomAlert("Uygulama kaynak kodundan çalıştırıldığı için güncelleme kontrolü geliştirici modunda yanıt verdi. Kurulu (.exe) sürümde güncellemeler otomatik olarak indirilir ve uygulanır.", "Geliştirici Modu");
                isManualCheck = false;
            }
        } else if (data.status === "available") {
            if (updateStatusText) {
                updateStatusText.innerHTML = `<i class="fa-solid fa-cloud-arrow-down" style="color: #3b82f6;"></i> Yeni sürüm bulundu (v${data.version || ''})! İndiriliyor...`;
                updateStatusText.style.color = "#3b82f6";
            }
            if (banner) {
                banner.style.display = "block";
                if (title) title.textContent = "Yeni Güncelleme Mevcut!";
                if (badge) {
                    badge.textContent = `v${data.version || ''}`;
                    badge.style.display = "inline-block";
                }
                if (desc) desc.textContent = "Güncelleme arka planda otomatik indiriliyor...";
                if (progContainer) progContainer.style.display = "block";
                if (progBar) progBar.style.width = "0%";
                if (progPercent) progPercent.textContent = "%0";
                if (actions) actions.style.display = "none";
                if (icon) icon.className = "fa-solid fa-cloud-arrow-down fa-bounce";
                if (iconWrapper) iconWrapper.className = "update-icon-wrapper";
            }
        } else if (data.status === "downloading") {
            const percent = data.percent || 0;
            if (updateStatusText) {
                updateStatusText.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="color: #3b82f6;"></i> Paket indiriliyor: %${percent}`;
            }
            if (banner) {
                banner.style.display = "block";
                if (progContainer) progContainer.style.display = "block";
                if (progBar) progBar.style.width = `${percent}%`;
                if (progPercent) progPercent.textContent = `%${percent}`;
                if (progLabel) progLabel.textContent = "İndiriliyor...";
                if (desc) desc.textContent = `Kurulum paketi indiriliyor (%${percent})...`;
            }
        } else if (data.status === "downloaded") {
            const ver = data.version ? `v${data.version}` : 'v1.1.9';
            isHotfixAction = false;
            if (updateStatusText) {
                updateStatusText.innerHTML = `<i class="fa-solid fa-circle-check" style="color: #10b981;"></i> Kurulum paketi hazır (${ver})! Yeniden başlatabilirsiniz.`;
                updateStatusText.style.color = "#10b981";
            }
            if (banner) {
                banner.style.display = "block";
                if (progContainer) progContainer.style.display = "none";
                if (title) title.textContent = "Kurulum Hazır!";
                if (badge) {
                    badge.textContent = ver;
                    badge.style.display = "inline-block";
                }
                if (desc) desc.textContent = "İndirme tamamlandı. Yenilikleri uygulamak için şimdi yeniden başlatın.";
                if (actions) {
                    actions.style.display = "flex";
                    btnRestart.innerHTML = '<i class="fa-solid fa-rotate-right"></i> Şimdi Güncelle & Yeniden Başlat';
                    btnRestart.disabled = false;
                }
                if (icon) icon.className = "fa-solid fa-circle-check";
                if (iconWrapper) iconWrapper.className = "update-icon-wrapper success";
            }
        } else if (data.status === "error") {
            console.error("AutoUpdater status error:", data.error);
            if (updateStatusText) {
                updateStatusText.innerHTML = `<i class="fa-solid fa-circle-exclamation" style="color: #ef4444;"></i> Güncelleme denetlenemedi: ${data.error || 'Bilinmeyen hata'}`;
                updateStatusText.style.color = "#ef4444";
            }
            if (isManualCheck) {
                showCustomAlert(`Güncelleme denetlenirken bir hata oluştu:\n${data.error || 'Sunucuya veya GitHub releases bağlantısı sağlanamadı.'}`, "Güncelleme Hatası");
                isManualCheck = false;
            }
        }
    });

    if (btnRestart) {
        btnRestart.addEventListener("click", () => {
            btnRestart.disabled = true;
            if (isHotfixAction) {
                btnRestart.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> İndiriliyor...';
                if (window.electronAPI.repairAndReinstall) {
                    window.electronAPI.repairAndReinstall();
                }
            } else {
                btnRestart.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Yeniden Başlatılıyor...';
                if (window.electronAPI.restartAndUpdate) {
                    window.electronAPI.restartAndUpdate();
                }
            }
        });
    }
}

/* ============================================================
   BYPASS SEKMESI - Tam Türkçe & Modernize Sürüm
   ============================================================ */
(function initBypass() {
    // --- Sabitler ---
    const BYPASS_JSON_URL = 'https://raw.githubusercontent.com/LightnigFast/Project-Lightning/main/bypass.json';
    const BYPASS_JSON_LOCAL = '/bypass_data.json';

    const SOFTWARE_LINKS = {
        'EA App': 'https://www.ea.com/ea-app',
        'Rockstar Games Launcher': 'https://socialclub.rockstargames.com/rockstar-games-launcher',
        'Ubisoft Connect': 'https://www.ubisoft.com/en-us/ubisoft-connect',
        'DirectX': 'https://www.microsoft.com/en-us/download/details.aspx?id=35',
        'DirectX 9': 'https://www.microsoft.com/en-us/download/details.aspx?id=35',
        'DirectX 11': 'https://www.microsoft.com/en-us/download/details.aspx?id=35',
        'DirectX 12': 'https://www.microsoft.com/en-us/download/details.aspx?id=35',
        'VC Redist': 'https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist',
        'VC Redist 2022': 'https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist',
        'Microsoft VC redistributable 2022': 'https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist',
        'Microsoft Visual C++ Redistributable': 'https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist',
        '.NET 4.6.2': 'https://dotnet.microsoft.com/en-us/download/dotnet-framework/net462',
        '.NET': 'https://dotnet.microsoft.com/en-us/download',
    };

    // Dinamik ve Kapsamlı Türkçe Çeviri Motoru
    function translateText(text) {
        if (!text) return '';
        let t = String(text).trim();

        // 1. Denuvo adımları
        let m = t.match(/^1\.\s*Install the game using files from ['"](.*?)['"]\.\s*If already installed, update via SteamTools\.?/i);
        if (m) return `1. Oyunu '${m[1]}' dosyalarıyla kurun. Zaten yüklüyse SteamTools ile güncelleyin.`;

        m = t.match(/^2\.\s*Open Project Lightning,\s*select (.*?),\s*and apply the fix to the game folder\.?/i);
        if (m) return `2. SteaMRogue Bypass sekmesinden ${m[1]} seçin ve 'Fix Uygula' butonuna basarak oyun klasörünüze kurun.`;

        m = t.match(/^3\.\s*Run (.*?)\.exe to generate the Denuvo ticket\.?/i);
        if (m) return `3. Denuvo bileti (ticket) oluşturmak için ${m[1]}.exe dosyasını çalıştırın.`;

        if (/^4\.\s*Send ['"]DenuvoTicket['"] file via request zone in my server/i.test(t)) {
            return "4. Oluşan 'DenuvoTicket' dosyasını talep kanalından gönderin.";
        }
        if (/^5\.\s*Replace ['"]DenuvoToken['"] in anadius\.cfg with the token I send you/i.test(t)) {
            return "5. anadius.cfg dosyasındaki 'DenuvoToken' kısmına size iletilen tokeni tırnakları koruyarak yapıştırın.";
        }

        m = t.match(/^6\.\s*Save the config and launch (.*?)\.exe\.?/i);
        if (m) return `6. Yapılandırmayı kaydedin ve ${m[1]}.exe dosyasını başlatın.`;

        if (/^If updated, send a new DenuvoTicket and repeat steps/i.test(t)) {
            return 'Oyun güncellenirse yeni bir DenuvoTicket oluşturup adımları tekrarlayın.';
        }

        // 2. Eksik bileşenler (DirectX, VC Redist, .NET, EA / Ubisoft Connect vb.)
        const installMatch = t.match(/^if the game shows errors when opening,\s*you need to install\s+(.+?)\.?$/i);
        if (installMatch) {
            let progs = installMatch[1];
            progs = progs.replace(/\band\b/gi, 've');
            progs = progs.replace(/DoNet|\.NET 4\.0|\.NET 4\.6\.2|\.NET/gi, '.NET Framework');
            progs = progs.replace(/VC Redist|Visual C\+\+|VC C\+\+|Microsoft Visual C\+\+ Redistributable|Microsoft VC redistributable/gi, 'Visual C++');
            progs = progs.replace(/Ubisoft Play|Ubisoft Connect/gi, 'Ubisoft Connect');
            progs = progs.replace(/EA Play|EA App/gi, 'EA App');
            progs = progs.replace(/Rockstar Games Launcher/gi, 'Rockstar Games Launcher');
            return `Oyun açılırken hata veriyorsa; ${progs} bileşenlerini kurmanız gerekir.`;
        }

        // 3. Easy Anti-Cheat ve Başlatma Seçenekleri
        if (/Play without Easy Anti-Cheat/i.test(t)) {
            return 'Oyunu Steam üzerinden başlatırken "Play without Easy Anti-Cheat" (Easy Anti-Cheat olmadan oyna) seçeneğini seçmelisiniz.';
        }

        m = t.match(/if you'?re still having issues,\s*simply go to the game folder and launch it using the\s+(.+?)\s+executable\.?/i);
        if (m) return `Sorun yaşamaya devam ederseniz oyun klasörüne gidip oyunu ${m[1]} dosyası ile başlatın.`;

        m = t.match(/to launch the game,\s*you need to use the\s+(.+?)\s+executable\s+included in the game's root folder\.?/i);
        if (m) return `Oyunu başlatmak için ana oyun klasöründeki ${m[1]} dosyasını kullanmalısınız.`;

        m = t.match(/the game is not compatible with steam,\s*it needs to be launched using the executable (?:called\s+)?(.+?)\s+inside the game folder\.?/i);
        if (m) return `Oyun doğrudan Steam ile uyumlu değildir; oyun klasöründeki ${m[1]} üzerinden başlatılmalıdır.`;

        if (/the game is not compatible with steam,\s*it needs to be launched using the executable inside the game folder\.?/i.test(t)) {
            return 'Oyun Steam ile uyumlu değildir; doğrudan oyun klasöründeki çalıştırılabilir (.exe) dosyasından başlatılmalıdır.';
        }

        m = t.match(/it is very important to launch the game using the\s+(.+?)\s+executable\.?/i);
        if (m) return `Oyunu mutlaka oyun klasöründeki ${m[1]} üzerinden başlatmalısınız.`;

        if (/it is very important to launch the game using the first \.exe you see in the folder/i.test(t)) {
            return 'Oyunu klasörde gördüğünüz ilk .exe dosyası ile başlatmanız çok önemlidir.';
        }

        m = t.match(/remember to launch the game with exe\s+(.+?)\s+inside the\s+(.+?)\s+folder\.?/i);
        if (m) return `Oyunu ${m[2]} klasöründeki ${m[1]} dosyası ile başlatmayı unutmayın.`;

        m = t.match(/it's important to launch the game using the executable named ['"](.*?)['"]\.?/i);
        if (m) return `Oyunu '${m[1]}' isimli dosya üzerinden başlatmanız önemlidir.`;

        m = t.match(/the game must be launched from the executable in the (?:game )?folder named ['"](.*?)['"]\.?/i);
        if (m) return `Oyun Steam üzerinden çalışmaz; mutlaka klasördeki '${m[1]}' dosyasından başlatılmalıdır.`;

        m = t.match(/the game does not work if you open it with steam,\s*you must open it with the exe called\s+(.+?)\s+that is inside the main folder of the game/i);
        if (m) return `Oyun Steam üzerinden çalışmaz; ana oyun klasöründeki ${m[1]} dosyasından açılmalıdır.`;

        m = t.match(/if the game doesn'?t launch with steam,\s*go to the main (?:game )?(?:folder|path) (?:of the game, )?and (?:launch|open) (?:the exe )?(.*?)\.?$/i);
        if (m) return `Oyun Steam ile açılmazsa ana oyun klasörüne gidip ${m[1]} dosyasını çalıştırın.`;

        m = t.match(/if the game dont launch,\s*open the game with the exe in the folder called\s+(.*?)\.?$/i);
        if (m) return `Oyun açılmazsa klasördeki ${m[1]} dosyasını çalıştırın.`;

        m = t.match(/if you cant open the game with steam,\s*try to open it with the exe in the folder called\s+(.*?)\.?$/i);
        if (m) return `Oyun Steam ile açılmazsa oyun klasöründeki ${m[1]} dosyasını açmayı deneyin.`;

        m = t.match(/you need to launch the game using the \*\*(.*?)\*\* executable\.?/i);
        if (m) return `Oyunu ${m[1]} dosyası ile başlatmanız gerekir.`;

        m = t.match(/you need to launch the game with the exe called\s+(.+?),\s*not with steam/i);
        if (m) return `Oyunu Steam ile değil, ${m[1]} dosyası ile başlatmanız gerekir.`;

        m = t.match(/you need to launch the game with the exe called\s+(.*?)\.?$/i);
        if (m) return `Oyunu ${m[1]} dosyası ile başlatmalısınız.`;

        m = t.match(/^open the game with\s+(.*?)\.?$/i);
        if (m) return `Oyunu ${m[1]} ile başlatın.`;

        m = t.match(/^the game opens with the exe \*(.*?)\*\.?$/i);
        if (m) return `Oyun ${m[1]} dosyası ile açılmaktadır.`;

        m = t.match(/to open the game,\s*you need to open the\s+(.+?)\s+file located inside the\s+(.+?)\s+folder\.?/i);
        if (m) return `Oyunu açmak için ${m[2]} klasöründeki ${m[1]} dosyasını çalıştırmalısınız.`;

        if (/for open the game,\s*use the bat called\s+(.*?)\.?$/i.test(t)) {
            const batM = t.match(/for open the game,\s*use the bat called\s+(.*?)\.?$/i);
            return `Oyunu açmak için ${batM ? batM[1] : '!start_cod.bat'} dosyasını çalıştırın.`;
        }

        if (/for play online,\s*execute the exe\s+(.*?)\.?$/i.test(t)) {
            const exeM = t.match(/for play online,\s*execute the exe\s+(.*?)\.?$/i);
            return `Çevrimiçi (online) oynamak için ${exeM ? exeM[1] : 'iw5mp.exe'} dosyasını çalıştırın.`;
        }

        // 4. Antivirüs ve Windows Defender Uyarıları
        if (/marking the game folder as an exception|mark the game folder as an exception|mark the game's folder as an exception/i.test(t)) {
            return 'Dosyaların silinmemesi için oyun klasörünü Windows Defender / Antivirüs dışlama listesine eklemeniz zorunludur.';
        }
        if (/antivirus will delete the\s+(.+?)\s+file/i.test(t)) {
            const antM = t.match(/antivirus will delete the\s+(.+?)\s+file/i);
            return `Antivirüs programınız ${antM ? antM[1] : 'gerekli'} dosyasını silebilir; bu dosya güvenilirdir ve fix için zorunludur.`;
        }
        if (/your antivirus may block the\s+(.+?)\s+file/i.test(t)) {
            const blkM = t.match(/your antivirus may block the\s+(.+?)\s+file/i);
            return `Antivirüsünüz ${blkM ? blkM[1] : 'gerekli'} dosyasını engelleyebilir; bu dosya tamamen güvenlidir. Fixin çalışması için izin vermelisiniz.`;
        }
        if (/it’s very likely that your antivirus will delete some files/i.test(t) || /possibly the antivirus deletes files/i.test(t)) {
            return 'Antivirüsünüz bazı fix dosyalarını silebilir. Oyun klasörünü dışlamalara ekleyin ve hata alırsanız fixi tekrar uygulayın.';
        }
        if (/remember to mark the game folder as an exception before applying the fix/i.test(t)) {
            return 'Fix uygulamadan önce oyun klasörünü antivirüs dışlama listesine eklemeyi unutmayın.';
        }

        // 5. Parsec / Çok Oyunculu / Co-op
        if (/Parsec application/i.test(t)) {
            return 'Arkadaşınızla birlikte oynamak için Parsec uygulamasını kullanabilirsiniz; arkadaşınız bilgisayarınıza ikinci bir kol bağlamış gibi bağlanabilir.';
        }
        if (/to play zombie mode,\s*you must enter multiplayer/i.test(t)) {
            return 'Zombi modunu oynamak için Multiplayer menüsüne girin ve Yerel Çok Oyunculu ekranında Sağ Ctrl + Z tuşlarına basın.';
        }
        if (/the game already includes the online fix/i.test(t)) {
            return 'Oyun online fix içermektedir, ancak arkadaşlarınızla oynayabilmek için hepinizin aynı son sürüme sahip olması gerekir.';
        }
        if (/this game only includes the campaign/i.test(t)) {
            return 'Bu fix yalnızca Hikaye (Campaign) modunu içerir. Zombi ve çok oyunculu modlar için Plutonium kullanmanız önerilir.';
        }

        // 6. Dil ve Diğer Özel Ayarlar
        m = t.match(/the fix is made in the Spanish language.*?access:\s*(.*?)\s*and open the \.ini file.*?Language=English/is);
        if (m) {
            return `Fix varsayılan olarak İspanyolcadır. İngilizce yapmak için '${m[1]}' klasöründeki .ini dosyasında Language=English ayarını yapabilirsiniz.`;
        }
        if (/open the localization\.txt file,\s*and change it to the language/i.test(t)) {
            return 'Oyun açılmazsa ana oyun klasöründeki localization.txt dosyasını açıp dil ayarını düzenleyin.';
        }
        if (/delete the steam\.txt file/i.test(t)) {
            return "Oyunu ilk kez başlatmadan önce ana oyun klasörüne gidip steam.txt dosyasını silmelisiniz, aksi takdirde oyun başlamaz.";
        }
        if (/STEAM MUST BE CLOSED before launching the game/i.test(t)) {
            return 'ÇOK ÖNEMLİ: Oyunu başlatmadan önce STEAM TAMAMEN KAPALI OLMALIDIR, aksi takdirde hata alırsınız.';
        }
        if (/game requires my manifest version|the game only works with my version of manifest|it will only work if you use my game manifests/i.test(t)) {
            return 'Oyunun çalışması için gerekli manifest sürümü gereklidir (Kütüphaneden indirebilirsiniz).';
        }
        if (/the game its a DLC,\s*and the fix is applied to the Call of Duty HQ folder/i.test(t)) {
            return 'Oyun bir DLC paketidir ve fix Call of Duty HQ klasörüne uygulanır.';
        }
        if (/only necessary to select Call of duty black ops 6 campaign DLC/i.test(t)) {
            return 'Call of Duty oyununda yalnızca Call of Duty Black Ops 6 Campaign DLC paketini seçmeniz yeterlidir.';
        }
        if (/MirrorsEdge\.exe.*?Windows XP \(Service Pack 3\)/i.test(t)) {
            return 'Oyun açılışta çökerse MirrorsEdge.exe dosyasına sağ tıklayıp Özellikler → Uyumluluk sekmesinden Windows XP (Service Pack 3) uyumluluk modunu seçin.';
        }
        if (/when you start the game,\s*a runtime error appears\.\s*Just click Ignore All/i.test(t)) {
            return 'Oyunu başlattığınızda bir çalışma zamanı (runtime) hatası çıkarsa sadece "Ignore All" (Tümünü Yoksay) butonuna tıklayın.';
        }
        if (/if the screen gets stuck on the Launching screen,\s*you just need to press ESC/i.test(t)) {
            return 'Ekran Başlatılıyor (Launching) kısmında takılı kalırsa klavyeden ESC tuşuna basın.';
        }
        if (/when I launched it for the first time through Steam,\s*it closed/i.test(t)) {
            return 'Steam ile ilk açılışta kapanırsa tekrar deneyin veya LIS2/Binaries/Win64/LIS2-Win64-Shipping.exe üzerinden başlatın.';
        }
        if (/when the game starts for the first time,\s*it usually takes a long time/i.test(t)) {
            return 'Oyun ilk açılışta uzun sürebilir; 5 dakika bekleyin, takılırsa kapatıp yeniden başlatın.';
        }
        if (/disable Windows\/driver updates to avoid issues/i.test(t)) {
            return 'Olası uyumluluk sorunlarını önlemek için Windows ve sürücü güncellemelerini duraklatın.';
        }
        if (/make sure you have the last CPU drivers/i.test(t)) {
            return 'En güncel işlemci (CPU) ve yonga seti sürücülerinin kurulu olduğundan emin olun.';
        }
        if (/the bypass does not have saved game for now/i.test(t)) {
            return 'Bypass şu an için kayıt (save) dosyalarını desteklememektedir, üzerinde çalışılıyor.';
        }
        if (/the game is so heavy,\s*I'm warning you/i.test(t)) {
            return 'Oyun dosya boyutu oldukça büyüktür, bilginize :)';
        }
        if (/support only via AnyDesk/i.test(t)) {
            return 'Destek yalnızca AnyDesk üzerinden sağlanmaktadır.';
        }
        if (/I know,\s*I know the fix is too large/i.test(t)) {
            return 'Fix boyutu biraz büyüktür ancak her şeyin sorunsuz çalışması için tüm dosyalar gereklidir.';
        }
        if (/enjoy the game|disfruta el juego/i.test(t)) {
            return 'İyi oyunlar dileriz! ♥';
        }
        if (/only ZEN Mode is available/i.test(t)) {
            return 'Yalnızca ZEN Modu mevcuttur (oyunun tek çevrimdışı modu).';
        }
        if (/game only works when launched through Steam/i.test(t)) {
            return 'Oyun yalnızca Steam üzerinden başlatıldığında çalışır.';
        }
        if (/graphics card is compatible with DirectX 12/i.test(t)) {
            return 'Ekran kartınızın DirectX 12 desteklemesi zorunludur, aksi halde oyun başlamayacaktır.';
        }
        if (/game takes a long time to load/i.test(t)) {
            return 'Oyunun açılması uzun sürebilir (10-15 dk), lütfen sabırla bekleyin.';
        }
        if (/to remove fps monitoring/i.test(t)) {
            return 'FPS göstergesini kapatmak için klavyeden birkaç kez "P" tuşuna basmanız yeterlidir.';
        }
        if (/you need to have the EA app installed|requires EA App running/i.test(t)) {
            return 'Bilgisayarınızda EA App kurulu ve açık olmalıdır, aksi halde oyun başlamaz.';
        }
        if (/requires Ubisoft Connect in offline mode/i.test(t)) {
            return 'Ubisoft Connect uygulamasının çevrimdışı modda açık olması gerekir.';
        }
        if (/no notes/i.test(t)) {
            return 'Özel bir kurulum notu bulunmuyor.';
        }

        return t;
    }

    // --- State ---
    let bypassData = null;
    let selectedCompany = null;
    let selectedGame = null;
    let currentCompanyEntries = [];
    const COMPANY_ORDER = ['UBISOFT', 'EA', 'ROCKSTAR', 'DENUVO', 'PlayStation'];
    let slideAnimationToken = 0;

    // --- DOM elemanları ---
    const mainView     = document.getElementById('bypass-main-view');
    const detailView   = document.getElementById('bypass-detail-view');
    const appsEl       = document.getElementById('bypass-apps');
    const stageEl      = document.getElementById('bypass-stage');
    const gamesSection = document.getElementById('bypass-games-section');
    const gamesGrid    = document.getElementById('bypass-games-grid');
    const loadingEl    = document.getElementById('bypass-loading');
    const companyLabel = document.getElementById('bypass-company-label');
    const gameCount    = document.getElementById('bypass-game-count');
    const searchInput  = document.getElementById('bypass-search-input');

    // Detay elemanları
    const backBtn          = document.getElementById('bypass-back-btn');
    const detailCover      = document.getElementById('bypass-detail-cover');
    const detailFixTag     = document.getElementById('bypass-detail-fix-tag');
    const detailTitle      = document.getElementById('bypass-detail-title');
    const detailAppid      = document.getElementById('bypass-detail-appid');
    const detailNote       = document.getElementById('bypass-detail-note');
    const detailErrors     = document.getElementById('bypass-detail-errors');
    const detailPrograms   = document.getElementById('bypass-detail-programs');
    const metaAppid        = document.getElementById('bypass-meta-appid');
    const metaExe          = document.getElementById('bypass-meta-exe');
    const metaSteam        = document.getElementById('bypass-meta-steam');
    const metaFix          = document.getElementById('bypass-meta-fix');
    const applyBtn         = document.getElementById('bypass-apply-btn');
    const applyBtnText     = document.getElementById('bypass-apply-btn-text');
    const applyStatus      = document.getElementById('bypass-apply-status');

    // Modal
    const defenderModal = document.getElementById('bypass-defender-modal');
    const modalYes      = document.getElementById('bypass-modal-yes');
    const modalNo       = document.getElementById('bypass-modal-no');

    // Bypass Choice Modal
    const bypassChoiceModal   = document.getElementById('bypass-choice-modal');
    const bypassChoiceClose   = document.getElementById('bypass-choice-close');
    const bypassChoiceCancel  = document.getElementById('bypass-choice-cancel');
    const btnBypassChoiceAuto = document.getElementById('btn-bypass-choice-auto');
    const btnBypassChoiceManual = document.getElementById('btn-bypass-choice-manual');

    // Toast stack
    const toastStack = document.getElementById('bypass-toast-stack');

    if (!appsEl || !mainView) return;

    // --- Toast Bildirimi ---
    function showBypassToast({ type = 'info', title = 'Bilgi', message = '' } = {}) {
        if (!toastStack) return;
        const t = document.createElement('div');
        t.className = `bypass-toast${type === 'error' ? ' is-error' : ''}`;
        t.innerHTML = `
            <div class="bypass-toast-bar"></div>
            <div>
                <div class="bypass-toast-title"></div>
                <div class="bypass-toast-msg"></div>
            </div>
            <button class="bypass-toast-close" type="button">&times;</button>
        `;
        t.querySelector('.bypass-toast-title').textContent = String(title);
        t.querySelector('.bypass-toast-msg').textContent = String(message);
        const close = () => t.remove();
        t.querySelector('.bypass-toast-close').addEventListener('click', close);
        toastStack.appendChild(t);
        setTimeout(close, type === 'error' ? 7000 : 4500);
    }

    // --- Caching ve Sabitler ---
    const COVER_CACHE_KEY = 'bypass_cover_';
    const COVER_CACHE_MEM = new Map();

    // --- Bypass JSON Yükle (Önce Yerel Hızlı JSON, Arka Planda Sessiz Güncelleme) ---
    async function loadBypassData() {
        if (bypassData) return bypassData;

        // 1. Önce yerel dosyadan anında yükle (0-5 ms gecikme)
        try {
            const res = await fetch(BYPASS_JSON_LOCAL);
            if (res.ok) {
                bypassData = await res.json();
                // Arka planda uzaktan güncel veri varsa sessizce yenile (kullanıcıyı bekletmez)
                fetch(BYPASS_JSON_URL + '?v=' + Date.now(), { signal: AbortSignal.timeout(6000) })
                    .then(r => r.ok ? r.json() : null)
                    .then(remoteData => {
                        if (remoteData && typeof remoteData === 'object') {
                            bypassData = remoteData;
                        }
                    })
                    .catch(() => {});
                return bypassData;
            }
        } catch (_) {}

        // 2. Yerel dosya bulunamazsa uzaktan yükle
        try {
            const res = await fetch(BYPASS_JSON_URL + '?v=' + Date.now(), { signal: AbortSignal.timeout(6000) });
            if (res.ok) {
                bypassData = await res.json();
                return bypassData;
            }
        } catch (_) {}

        return null;
    }

    // --- Spotlight Pozisyonu ---
    function updateSpotlight(tile) {
        if (!stageEl || !tile) return;
        const color = tile.dataset.color || '#3B82F6';
        stageEl.style.setProperty('--spot-color', color);
        stageEl.style.setProperty('--spot-opacity', '0.95');
        const tr = tile.getBoundingClientRect();
        const x = tr.left + tr.width / 2;
        const y = tr.top + tr.height / 2;
        stageEl.style.setProperty('--spot-x', `${Math.round(x)}px`);
        stageEl.style.setProperty('--spot-y', `${Math.round(y)}px`);
        tile.style.setProperty('--tile-color', color);
    }

    // --- Kapak Görseli Akıllı Doğrulanmış Override Haritası ---
    // Steam 600x900 kütüphane kapağı olmayan oyunların çalışan orijinal yüksek çözünürlüklü kapakları
    const COVER_OVERRIDES = {
        '241560': 'https://cdn.cloudflare.steamstatic.com/steam/apps/241560/header.jpg',
        '242550': 'https://cdn.cloudflare.steamstatic.com/steam/apps/242550/header.jpg',
        '201870': 'https://cdn.cloudflare.steamstatic.com/steam/apps/201870/header.jpg',
        '911400': 'https://cdn.cloudflare.steamstatic.com/steam/apps/911400/header.jpg',
        '354380': 'https://cdn.cloudflare.steamstatic.com/steam/apps/354380/header.jpg',
        '359610': 'https://cdn.cloudflare.steamstatic.com/steam/apps/359610/header.jpg',
        '233270': 'https://cdn.cloudflare.steamstatic.com/steam/apps/233270/header.jpg',
        '446560': 'https://cdn.cloudflare.steamstatic.com/steam/apps/446560/header.jpg',
        '33440': 'https://cdn.cloudflare.steamstatic.com/steam/apps/33440/header.jpg',
        '243470': 'https://cdn.cloudflare.steamstatic.com/steam/apps/243470/header.jpg',
        '235600': 'https://cdn.cloudflare.steamstatic.com/steam/apps/235600/header.jpg',
        '3405690': 'https://cdn.cloudflare.steamstatic.com/steam/apps/3405690/library_hero.jpg',
        '3059520': 'https://cdn.cloudflare.steamstatic.com/steam/apps/3059520/library_hero.jpg',
        '1222680': 'https://cdn.cloudflare.steamstatic.com/steam/apps/1222680/library_hero.jpg',
        '3654560': 'https://cdn.cloudflare.steamstatic.com/steam/apps/3654560/library_hero.jpg',
        '3768760': 'https://cdn.cloudflare.steamstatic.com/steam/apps/3768760/library_hero.jpg',
        '2215200': 'https://cdn.cloudflare.steamstatic.com/steam/apps/2215200/library_hero.jpg',
        '1941540': 'https://cdn.cloudflare.steamstatic.com/steam/apps/1941540/library_hero.jpg',
        '3357650': 'https://cdn.cloudflare.steamstatic.com/steam/apps/3357650/library_hero.jpg',
        '3764200': 'https://cdn.cloudflare.steamstatic.com/steam/apps/3764200/library_hero.jpg',
        '2806050': 'https://cdn.cloudflare.steamstatic.com/steam/apps/2806050/library_hero.jpg',
        '115300': 'https://cdn.cloudflare.steamstatic.com/steam/apps/115300/library_hero.jpg',
        '3595230': 'https://cdn.cloudflare.steamstatic.com/steam/apps/3595230/library_hero.jpg',
        '3595270': 'https://cdn.cloudflare.steamstatic.com/steam/apps/3595270/library_hero.jpg',
        '2933620': 'https://cdn.cloudflare.steamstatic.com/steam/apps/2933620/header.jpg',
        '255480': 'https://cdn.cloudflare.steamstatic.com/steam/apps/255480/header.jpg',
        '224060': 'https://cdn.cloudflare.steamstatic.com/steam/apps/224060/header.jpg',
        '3751950': 'https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/3751950/36a1644b03afce1a648ab90b232196609e827539/library_capsule.jpg',
        '3940610': 'https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/3940610/265d9223cba1401f91e9cc711ebe3a5f5e3440b8/library_capsule.jpg',
        '4032350': 'https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/4032350/0d18c22e927cc6fe246d6a0412c87096ff33c00a/library_capsule.jpg',
        '4356430': 'https://cdn2.steamgriddb.com/grid/41f111384c98a213f4b187cf3e952245.png',
        '3265250': 'https://cdn.cloudflare.steamstatic.com/steam/apps/3265250/header.jpg'
    };

    function applyCropStyle(img, src) {
        const isHero = src && (src.includes('library_hero') || src.includes('header.jpg') || src.includes('capsule_616x353') || src.includes('library_capsule') || src.includes('.png'));
        if (isHero) {
            img.style.objectFit = 'cover';
            img.style.objectPosition = 'center top';
        }
    }

    function loadCoverWithFallback(img, appid, game) {
        img.loading = 'lazy';
        img.decoding = 'async';

        const strAppid = String(appid);

        // 1. RAM Önbelleği (0 ms)
        if (COVER_CACHE_MEM.has(strAppid)) {
            const cached = COVER_CACHE_MEM.get(strAppid);
            img.src = cached;
            img.style.opacity = '1';
            applyCropStyle(img, cached);
            return;
        }

        // 2. Kalıcı Yerel Hafıza (0 ms)
        try {
            const localSaved = localStorage.getItem(COVER_CACHE_KEY + strAppid);
            if (localSaved) {
                COVER_CACHE_MEM.set(strAppid, localSaved);
                img.src = localSaved;
                img.style.opacity = '1';
                applyCropStyle(img, localSaved);
                return;
            }
        } catch (_) {}

        const custom = game ? game.custom_images : null;
        const customUrl = custom?.cover_image || custom?.hero_image_x2 || custom?.background;
        const override = COVER_OVERRIDES[strAppid];

        // Öncelik sırası:
        // Doğrulanmış Override varsa ilk onu dener (404 beklemesi olmaz)
        // Yoksa orijinal yüksek kaliteli 600x900 Cloudflare Steam CDN ilk denenir
        const sources = override ? [
            override,
            customUrl,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/library_600x900.jpg`,
            `https://cdn.akamai.steamstatic.com/steam/apps/${appid}/library_600x900.jpg`,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/library_hero.jpg`,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/header.jpg`,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/capsule_616x353.jpg`,
        ].filter(Boolean) : [
            customUrl,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/library_600x900.jpg`,
            `https://cdn.akamai.steamstatic.com/steam/apps/${appid}/library_600x900.jpg`,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/library_hero.jpg`,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/header.jpg`,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/capsule_616x353.jpg`,
        ].filter(Boolean);

        let idx = 0;
        function tryNext() {
            if (idx >= sources.length) {
                img.style.display = 'none';
                return;
            }
            const src = sources[idx++];
            img.onload = () => {
                img.style.opacity = '1';
                applyCropStyle(img, src);
                COVER_CACHE_MEM.set(strAppid, src);
                try {
                    localStorage.setItem(COVER_CACHE_KEY + strAppid, src);
                } catch (_) {}
            };
            img.onerror = () => tryNext();
            img.src = src;
        }
        tryNext();
    }

    // --- Detay Hero Görseli Fallback Zinciri ---
    function loadHeroWithFallback(imgEl, appid, game) {
        imgEl.loading = 'lazy';
        imgEl.decoding = 'async';
        imgEl.style.opacity = '0';
        const strAppid = String(appid);

        const custom = game ? game.custom_images : null;
        const customHero = custom?.hero_image_x2 || custom?.background || custom?.cover_image;
        const override = COVER_OVERRIDES[strAppid];

        const sources = [
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/library_hero.jpg`,
            `https://cdn.akamai.steamstatic.com/steam/apps/${appid}/library_hero.jpg`,
            override,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/header.jpg`,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/capsule_616x353.jpg`,
            `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/library_600x900.jpg`,
            customHero,
        ].filter(Boolean);

        let idx = 0;
        function tryNext() {
            if (idx >= sources.length) {
                imgEl.style.opacity = '0';
                return;
            }
            const src = sources[idx++];
            imgEl.onload = () => {
                imgEl.style.opacity = '1';
            };
            imgEl.onerror = () => tryNext();
            imgEl.src = src;
        }
        tryNext();
    }

    // --- Şirket Oyunlarını Göster (Dinamik Kayma & Çoklu Sayfa Hız Efekti) ---
    async function showCompanyGames(companyKey) {
        const prevCompany = selectedCompany;
        selectedCompany = companyKey;

        if (searchInput) searchInput.value = '';

        const data = await loadBypassData();

        if (!data || (!data[companyKey] && companyKey !== 'PlayStation')) {
            showBypassToast({ type: 'error', title: 'Hata', message: 'Oyun verileri yüklenemedi.' });
            return;
        }

        let newEntries = [];
        let newLabel = companyKey;

        if (companyKey === 'PlayStation') {
            const ps = (data && data['PlayStation']) || {};
            const oth = (data && (data['OTHERS'] || data['others'])) || {};
            newEntries = [...Object.entries(ps), ...Object.entries(oth)];
            newLabel = 'PlayStation';
        } else {
            const company = data[companyKey] || {};
            newEntries = Object.entries(company);
            newLabel = companyKey;
        }

        currentCompanyEntries = newEntries;

        const isFirstOpen = !prevCompany || gamesSection.style.display === 'none' || !gamesSection.classList.contains('is-visible');

        if (isFirstOpen) {
            companyLabel.textContent = newLabel;
            gameCount.textContent = `${newEntries.length} Oyun`;
            gamesSection.style.display = 'flex';
            void gamesSection.offsetHeight;
            gamesSection.classList.add('is-visible');
            gamesGrid.style.transform = 'none';
            gamesGrid.style.opacity = '1';
            gamesGrid.style.filter = 'none';
            renderGamesGrid(newEntries);
            return;
        }

        // Kullanıcı aynı sekmeye tekrar tıklamışsa animasyon yapma
        if (prevCompany === companyKey) return;

        // --- Çoklu Sayfa Geçiş Hesabı & Dinamik Efekt ---
        const prevIdx = COMPANY_ORDER.indexOf(prevCompany);
        const newIdx = COMPANY_ORDER.indexOf(companyKey);
        const delta = (prevIdx !== -1 && newIdx !== -1) ? (newIdx - prevIdx) : 1;
        const distance = Math.max(1, Math.abs(delta));
        const dir = delta >= 0 ? 1 : -1; // 1: sağa geçiş (içerik sola kayar), -1: sola geçiş (içerik sağa kayar)

        // Atlama mesafesine göre dinamik piksel mesafesi, hız ve hareket bulanıklığı (motion blur)
        const baseOffset = 80;
        const slideOffset = Math.min(320, baseOffset * distance);
        const duration = 280 + Math.min(180, distance * 45);
        const blurAmount = Math.min(6, 1.4 * distance);

        const currentToken = ++slideAnimationToken;

        // 1. Aşama: Mevcut oyunlar ters yöne doğru kayar ve kaybolur
        const outTime = Math.round(duration * 0.42);
        gamesGrid.style.transition = `transform ${outTime}ms cubic-bezier(0.4, 0, 0.7, 1), opacity ${Math.round(duration * 0.38)}ms ease, filter ${Math.round(duration * 0.38)}ms ease`;
        gamesGrid.style.transform = `translateX(${-dir * Math.round(slideOffset * 0.42)}px) scale(0.975)`;
        gamesGrid.style.opacity = '0';
        gamesGrid.style.filter = `blur(${blurAmount}px)`;

        companyLabel.style.transition = `transform ${Math.round(duration * 0.35)}ms ease, opacity ${Math.round(duration * 0.3)}ms ease`;
        companyLabel.style.transform = `translateX(${-dir * 25}px)`;
        companyLabel.style.opacity = '0';

        gameCount.style.transition = `opacity ${Math.round(duration * 0.3)}ms ease`;
        gameCount.style.opacity = '0';

        setTimeout(() => {
            if (currentToken !== slideAnimationToken) return;

            // 2. Aşama: Başlık ve yeni oyunlar render edilir
            companyLabel.textContent = newLabel;
            gameCount.textContent = `${newEntries.length} Oyun`;
            renderGamesGrid(newEntries);

            // Yeni içeriği gelen yöne hazırla (anlık geçiş, animasyonsuz)
            gamesGrid.style.transition = 'none';
            gamesGrid.style.transform = `translateX(${dir * slideOffset}px) scale(0.975)`;
            gamesGrid.style.opacity = '0';
            gamesGrid.style.filter = `blur(${blurAmount}px)`;

            companyLabel.style.transition = 'none';
            companyLabel.style.transform = `translateX(${dir * 25}px)`;
            companyLabel.style.opacity = '0';

            // Reflow tetikle
            void gamesGrid.offsetWidth;
            void companyLabel.offsetWidth;

            // 3. Aşama: Yeni oyunlar kayarak, pürüzsüzce oturur (GPU hızlandırmalı)
            const inTime = Math.round(duration * 0.58);
            gamesGrid.style.transition = `transform ${inTime}ms cubic-bezier(0.16, 1, 0.3, 1), opacity ${Math.round(duration * 0.52)}ms cubic-bezier(0.16, 1, 0.3, 1), filter ${Math.round(duration * 0.52)}ms ease`;
            gamesGrid.style.transform = 'translateX(0) scale(1)';
            gamesGrid.style.opacity = '1';
            gamesGrid.style.filter = 'blur(0)';

            companyLabel.style.transition = `transform ${Math.round(duration * 0.5)}ms cubic-bezier(0.16, 1, 0.3, 1), opacity ${Math.round(duration * 0.5)}ms ease`;
            companyLabel.style.transform = 'translateX(0)';
            companyLabel.style.opacity = '1';

            gameCount.style.transition = `opacity ${Math.round(duration * 0.5)}ms ease`;
            gameCount.style.opacity = '1';
        }, outTime);
    }

    // --- Grid Render Fonksiyonu ---
    function renderGamesGrid(entries) {
        gamesGrid.innerHTML = '';
        if (entries.length === 0) {
            gamesGrid.innerHTML = '<div style="grid-column: 1/-1; padding: 40px; text-align: center; color: rgba(255,255,255,0.4); font-size: 0.9rem;">Aramanızla eşleşen oyun bulunamadı.</div>';
            return;
        }

        entries.forEach(([appid, game]) => {
            const card = document.createElement('button');
            card.type = 'button';
            card.className = 'bypass-game-card';
            card.dataset.appid = appid;

            const nameEl = document.createElement('span');
            nameEl.className = 'bypass-game-name';
            nameEl.textContent = game.name || appid;
            card.appendChild(nameEl);

            const img = document.createElement('img');
            img.alt = game.name || '';
            img.style.opacity = '0';
            card.insertBefore(img, card.firstChild);
            loadCoverWithFallback(img, appid, game);

            card.addEventListener('click', () => openBypassDetail(appid, game));
            gamesGrid.appendChild(card);
        });
    }

    // --- Arama Filtreleme ---
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim().toLowerCase();
            if (!query) {
                renderGamesGrid(currentCompanyEntries);
                gameCount.textContent = `${currentCompanyEntries.length} Oyun`;
                return;
            }

            const filtered = currentCompanyEntries.filter(([appid, game]) => {
                const name = (game.name || '').toLowerCase();
                const fix = (game.nombre_fix || '').toLowerCase();
                return name.includes(query) || appid.includes(query) || fix.includes(query);
            });

            renderGamesGrid(filtered);
            gameCount.textContent = `${filtered.length} / ${currentCompanyEntries.length} Oyun`;
        });
    }

    // --- Detay Ekranını Aç ---
    function openBypassDetail(appid, game) {
        selectedGame = { appid, ...game };

        mainView.style.display = 'none';
        detailView.style.display = 'flex';

        // Hero Görseli
        loadHeroWithFallback(detailCover, appid, game);

        // Başlık ve Etiketler
        detailFixTag.textContent = game.nombre_fix || game.fix_name || 'Bypass Fix';
        detailTitle.textContent = game.name || appid;
        detailAppid.textContent = appid;
        metaAppid.textContent = appid;

        // Notlar (Türkçe)
        detailNote.textContent = translateText(game.comentarios || game.notes) || 'Bu oyun için özel bir not bulunmuyor. İyi oyunlar!';

        // Bilinen Sorunlar (Türkçe)
        detailErrors.innerHTML = '';
        if (Array.isArray(game.errores) && game.errores.length > 0) {
            game.errores.forEach((err, i) => {
                const li = document.createElement('li');
                li.className = 'bypass-error-item';
                li.innerHTML = `<span class="bypass-error-num">${String(i+1).padStart(2,'0')}</span><span>${translateText(err)}</span>`;
                detailErrors.appendChild(li);
            });
            document.getElementById('bypass-detail-errors-wrap').style.display = '';
        } else {
            document.getElementById('bypass-detail-errors-wrap').style.display = 'none';
        }

        // Gerekli Yazılımlar (Türkçe Etiketler)
        detailPrograms.innerHTML = '';
        if (Array.isArray(game.programas_necesarios) && game.programas_necesarios.length > 0) {
            game.programas_necesarios.forEach(p => {
                const li = document.createElement('li');
                li.className = 'bypass-program-item';
                li.innerHTML = `<i class="fa-solid fa-download" style="color:#a855f7;font-size:0.75rem;"></i> <span>${p}</span>`;
                const url = SOFTWARE_LINKS[p.trim()];
                if (url) {
                    li.style.cursor = 'pointer';
                    li.title = `${p} indirmek için tıkla`;
                    li.addEventListener('click', () => window.open(url, '_blank', 'noopener'));
                }
                detailPrograms.appendChild(li);
            });
            document.getElementById('bypass-detail-software-wrap').style.display = '';
        } else {
            document.getElementById('bypass-detail-software-wrap').style.display = 'none';
        }

        // Meta Yapılandırma
        metaExe.textContent = game.launch_exe ? 'Evet' : 'Hayır';
        metaExe.className = `bypass-meta-val ${game.launch_exe ? 'ok' : 'no'}`;
        metaSteam.textContent = game.launch_steam ? 'Evet' : 'Hayır';
        metaSteam.className = `bypass-meta-val ${game.launch_steam ? 'ok' : 'no'}`;
        metaFix.textContent = game.nombre_fix || game.fix_name || 'Standart Bypass';

        resetApplyBtn();
    }

    // --- Geri Butonu ---
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            detailView.style.display = 'none';
            mainView.style.display = 'flex';
            resetApplyBtn();
        });
    }

    // --- Apply Butonu Sıfırla ---
    function resetApplyBtn() {
        if (!applyBtn) return;
        applyBtn.disabled = false;
        applyBtn.classList.remove('done');
        applyBtnText.textContent = 'Fix Uygula';
        applyStatus.textContent = '';
    }

    // --- Windows Defender Modalı ---
    function showDefenderModal() {
        return new Promise(resolve => {
            if (!defenderModal) { resolve(true); return; }
            defenderModal.style.display = 'flex';
            const cleanup = () => { defenderModal.style.display = 'none'; };
            const onYes = () => { cleanup(); modalYes.removeEventListener('click', onYes); modalNo.removeEventListener('click', onNo); resolve(true); };
            const onNo  = () => {
                cleanup(); modalYes.removeEventListener('click', onYes); modalNo.removeEventListener('click', onNo);
                showBypassToast({ type: 'error', title: 'İşlem İptal Edildi', message: 'Defender istisnası eklenmeden fix uygulanmadı.' });
                resolve(false);
            };
            modalYes.addEventListener('click', onYes);
            modalNo.addEventListener('click', onNo);
        });
    }

    // --- Bypass Kurulum Seçenek Modalı (Otomatik / Manuel) ---
    function showBypassChoiceModal() {
        return new Promise(resolve => {
            if (!bypassChoiceModal) { resolve('manual'); return; }
            bypassChoiceModal.style.display = 'flex';
            const cleanup = () => { bypassChoiceModal.style.display = 'none'; };

            const onAuto = () => { cleanup(); removeListeners(); resolve('auto'); };
            const onManual = () => { cleanup(); removeListeners(); resolve('manual'); };
            const onCancel = () => { cleanup(); removeListeners(); resolve(null); };

            function removeListeners() {
                if (btnBypassChoiceAuto) btnBypassChoiceAuto.removeEventListener('click', onAuto);
                if (btnBypassChoiceManual) btnBypassChoiceManual.removeEventListener('click', onManual);
                if (bypassChoiceClose) bypassChoiceClose.removeEventListener('click', onCancel);
                if (bypassChoiceCancel) bypassChoiceCancel.removeEventListener('click', onCancel);
            }

            if (btnBypassChoiceAuto) btnBypassChoiceAuto.addEventListener('click', onAuto);
            if (btnBypassChoiceManual) btnBypassChoiceManual.addEventListener('click', onManual);
            if (bypassChoiceClose) bypassChoiceClose.addEventListener('click', onCancel);
            if (bypassChoiceCancel) bypassChoiceCancel.addEventListener('click', onCancel);
        });
    }

    // --- Fix Uygulama Akışı (Otomatik & Manuel) ---
    async function applyFixFlow() {
        if (!selectedGame) return;
        const game = selectedGame;
        const appid = String(game.appid);

        // 1. Defender uyarısı gerekiyorsa sor
        const needExclusion = game.exclusion === true || game.exclusion === 'yes' || game.exclusion === 'true';
        if (needExclusion) {
            const ok = await showDefenderModal();
            if (!ok) return;
        }

        // 2. Yöntem Seçimi (Otomatik mi yoksa Manuel mi?)
        const choice = await showBypassChoiceModal();
        if (!choice) {
            resetApplyBtn();
            return;
        }

        applyBtn.disabled = true;
        applyStatus.textContent = '';
        let destDir = null;

        if (choice === 'auto') {
            applyBtnText.textContent = 'Oyun klasörü taranıyor...';
            applyStatus.textContent = 'Tüm disklerdeki (C:, D:, E: vb.) Steam kütüphaneleri taranıyor...';

            try {
                const searchRes = await fetch('/api/find_game_folder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ appid, name: game.name })
                });
                const searchData = await searchRes.json();

                if (searchData.ok && searchData.path) {
                    destDir = searchData.path;
                    showBypassToast({
                        type: 'info',
                        title: 'Oyun Otomatik Bulundu',
                        message: `Klasör: ${destDir}`
                    });
                } else {
                    // Otomatik bulunamadıysa kullanıcıya güvenli fallback sun
                    const fallbackManual = await showCustomConfirm(
                        `"${game.name}" oyunu bilgisayarınızdaki Steam kütüphanelerinde (C:, D:, E: vb.) otomatik tespit edilemedi.\n\n` +
                        `Oyununuz yüklüyse veya farklı bir klasöre kurulduysa, klasörü şimdi kendiniz seçmek ister misiniz?`,
                        "Oyun Klasörü Bulunamadı",
                        "Klasörü Seç",
                        "İptal"
                    );
                    if (fallbackManual) {
                        applyBtnText.textContent = 'Oyun klasörü seçiliyor...';
                        applyStatus.textContent = 'Lütfen oyun klasörünüzü seçin...';
                        const selRes = await fetch(`/api/select_folder?title=${encodeURIComponent(`${game.name} oyun klasörünü seç`)}`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ initialdir: searchData.default_common })
                        });
                        const selJson = await selRes.json();
                        if (!selJson.path) {
                            resetApplyBtn();
                            return;
                        }
                        destDir = selJson.path;
                    } else {
                        resetApplyBtn();
                        return;
                    }
                }
            } catch (e) {
                showBypassToast({ type: 'error', title: 'Tarama Hatası', message: String(e) });
                resetApplyBtn();
                return;
            }
        } else {
            // Manuel Seçim
            applyBtnText.textContent = 'Oyun klasörü seçiliyor...';
            applyStatus.textContent = 'Steam kütüphanesi açılıyor...';

            try {
                // Önceden en uygun common klasörünü al (varsa D:\SteamLibrary, yoksa C:\)
                const preRes = await fetch('/api/find_game_folder', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ appid, name: game.name })
                });
                const preData = await preRes.json();
                const initDir = preData.path ? preData.path : preData.default_common;

                const res = await fetch(`/api/select_folder?title=${encodeURIComponent(`${game.name} oyun klasörünü seç`)}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ initialdir: initDir })
                });
                const json = await res.json();
                if (!json.path) {
                    resetApplyBtn();
                    return;
                }
                destDir = json.path;
            } catch (e) {
                showBypassToast({ type: 'error', title: 'Hata', message: 'Klasör seçimi başarısız oldu.' });
                resetApplyBtn();
                return;
            }
        }

        if (!destDir) {
            resetApplyBtn();
            return;
        }

        const normalized = destDir.toLowerCase().replace(/\\/g, '/');
        if (!normalized.includes('steamapps/common')) {
            const proceedAnyway = await showCustomConfirm(
                "Seçilen klasör 'steamapps/common' altında görünmüyor:\n\n" + destDir +
                "\n\nYine de bu klasöre fix uygulamak istediğinize emin misiniz?",
                "Klasör Uyarısı",
                "Yine de Devam Et",
                "İptal"
            );
            if (!proceedAnyway) {
                resetApplyBtn();
                return;
            }
        }

        applyBtnText.textContent = 'Fix indiriliyor ve kuruluyor...';
        applyStatus.textContent = 'Lütfen bekleyin, arşiv çıkartılıyor...';

        try {
            const res = await fetch('/api/apply_fix', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ appid, dest_dir: destDir, game })
            });
            const json = await res.json();

            if (json.ok) {
                applyBtn.classList.add('done');
                applyBtnText.textContent = 'Fix Başarıyla Uygulandı!';
                applyBtn.disabled = true;
                applyStatus.textContent = `İşlem tamamlandı (${destDir}).`;
                showBypassToast({ type: 'info', title: 'Başarılı!', message: `${game.name} için fix başarıyla kuruldu.` });
            } else {
                showBypassToast({ type: 'error', title: 'Fix Uygulama Hatası', message: json.message || 'Fix uygulanamadı.' });
                resetApplyBtn();
            }
        } catch (e) {
            showBypassToast({ type: 'error', title: 'Bağlantı Hatası', message: String(e.message || e) });
            resetApplyBtn();
        }
    }

    if (applyBtn) applyBtn.addEventListener('click', applyFixFlow);

    // --- Tile Tıklama ve Hover ---
    const tiles = Array.from(appsEl.querySelectorAll('.bypass-app'));
    tiles.forEach(tile => {
        const color = tile.dataset.color;
        if (color) tile.style.setProperty('--tile-color', color);

        tile.addEventListener('mouseenter', () => updateSpotlight(tile));
        tile.addEventListener('click', () => {
            const wasActive = tile.classList.contains('is-active');
            if (wasActive) {
                tile.classList.remove('is-active');
                stageEl.classList.remove('has-selection');
                gamesSection.classList.remove('is-visible');
                stageEl.style.setProperty('--spot-opacity', '0');
                selectedCompany = null;
                
                let start = performance.now();
                function trackClose() {
                    if (performance.now() - start < 450) {
                        requestAnimationFrame(trackClose);
                    } else {
                        if (!selectedCompany) {
                            gamesSection.style.display = 'none';
                        }
                    }
                }
                requestAnimationFrame(trackClose);
                return;
            }
            tiles.forEach(t => t.classList.remove('is-active'));
            tile.classList.add('is-active');
            stageEl.classList.add('has-selection');
            updateSpotlight(tile);

            let start = performance.now();
            function trackOpen() {
                updateSpotlight(tile);
                if (performance.now() - start < 450) {
                    requestAnimationFrame(trackOpen);
                }
            }
            requestAnimationFrame(trackOpen);

            showCompanyGames(tile.dataset.app);
        });
    });

    if (appsEl) {
        appsEl.addEventListener('mouseleave', () => {
            const at = appsEl.querySelector('.bypass-app.is-active');
            if (at) {
                updateSpotlight(at);
            } else if (stageEl) {
                stageEl.style.setProperty('--spot-opacity', '0');
            }
        });

        const activeTile = appsEl.querySelector('.bypass-app.is-active');
        if (activeTile) {
            requestAnimationFrame(() => updateSpotlight(activeTile));
        } else if (stageEl) {
            stageEl.classList?.remove('has-selection');
            stageEl.style?.setProperty?.('--spot-opacity', '0');
        }
    }

    window.addEventListener('resize', () => {
        const at = appsEl ? appsEl.querySelector('.bypass-app.is-active') : null;
        if (at) updateSpotlight(at);
    });

    document.querySelectorAll('.nav-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.dataset.tab === 'bypass') {
                setTimeout(() => {
                    const at = appsEl ? appsEl.querySelector('.bypass-app.is-active') : null;
                    if (at) {
                        updateSpotlight(at);
                    } else if (stageEl) {
                        stageEl.style?.setProperty?.('--spot-opacity', '0');
                    }
                }, 60);
            }
        });
    });

    const scrollContainer = document.querySelector('.app-main');
    if (scrollContainer) {
        scrollContainer.addEventListener('scroll', () => {
            const at = appsEl.querySelector('.bypass-app.is-active');
            if (at) updateSpotlight(at);
        }, { passive: true });
    }

    // Uygulama açılışında veriyi arka planda önceden hafızaya al (0 ms anlık açılış)
    loadBypassData();

})();

// ==========================================================================
// SAM (Steam Achievement Manager) Controller & UI Handlers
// ==========================================================================
let samLibraryLoaded = false;
let samAllGames = [];
let samGridListenerBound = false;
let samCurrentAppId = null;
let samCurrentAppName = "";
let samCurrentAchievements = [];
let samModalEventsBound = false;

function initSAM() {
    const searchInput = document.getElementById("sam-search-input");
    const btnRefresh = document.getElementById("btn-sam-refresh-library");

    function escapeSAMHtml(text) {
        if (!text) return "";
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function updateSAMModalStats() {
        const totalEl = document.getElementById("sam-modal-total-count");
        const unlockedEl = document.getElementById("sam-modal-unlocked-count");
        const percentEl = document.getElementById("sam-modal-percent");
        const progressEl = document.getElementById("sam-modal-progress-bar");

        const total = samCurrentAchievements.length;
        const unlocked = samCurrentAchievements.filter(a => a.achieved).length;
        const percent = total > 0 ? Math.round((unlocked / total) * 100) : 0;

        if (totalEl) totalEl.textContent = total;
        if (unlockedEl) unlockedEl.textContent = unlocked;
        if (percentEl) percentEl.textContent = `%${percent}`;
        if (progressEl) progressEl.style.width = `${percent}%`;
    }

    function renderSAMAchievementsList(filterQuery = "") {
        const container = document.getElementById("sam-modal-achievements-container");
        const filterCountEl = document.getElementById("sam-modal-filter-count");
        if (!container) return;

        const q = (filterQuery || "").toLowerCase().trim();
        let list = samCurrentAchievements;
        if (q) {
            list = samCurrentAchievements.filter(a => 
                (a.name || "").toLowerCase().includes(q) ||
                (a.desc || "").toLowerCase().includes(q) ||
                (a.id || "").toLowerCase().includes(q)
            );
        }

        if (filterCountEl) {
            filterCountEl.textContent = `Görüntülenen: ${list.length} / ${samCurrentAchievements.length}`;
        }

        if (!list || list.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 45px 20px; color: var(--text-muted);">
                    <i class="fa-solid fa-trophy" style="font-size: 2.2rem; color: rgba(124, 58, 237, 0.3); margin-bottom: 12px; display: block;"></i>
                    <p style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary);">
                        ${q ? 'Aramanızla Eşleşen Başarım Bulunamadı' : 'Bu Oyun İçin Başarım Bulunamadı'}
                    </p>
                    <p style="font-size: 0.8rem; margin-top: 4px;">
                        ${q ? 'Farklı bir anahtar kelime aramayı deneyin.' : 'Bu oyunda Steam başarımı tanımlanmamış olabilir.'}
                    </p>
                </div>
            `;
            return;
        }

        const html = list.map(ach => {
            const isAchieved = !!ach.achieved;
            const iconFile = isAchieved ? (ach.icon || ach.icon_locked) : (ach.icon_locked || ach.icon);
            const iconUrl = iconFile ? `https://cdn.steamstatic.com/steamcommunity/public/images/apps/${samCurrentAppId}/${iconFile}` : "icon.ico";
            
            return `
                <div class="sam-ach-item ${isAchieved ? 'achieved' : ''}" data-id="${escapeSAMHtml(ach.id)}">
                    <div style="display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0;">
                        <img src="${iconUrl}" class="sam-ach-icon" loading="lazy" onerror="this.src='icon.ico'">
                        <div style="min-width: 0; padding-right: 12px;">
                            <div style="font-weight: 700; font-size: 0.92rem; color: #fff; margin-bottom: 3px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
                                ${escapeSAMHtml(ach.name || ach.id)}
                            </div>
                            <div style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.35;">
                                ${escapeSAMHtml(ach.desc || '(Gizli Başarım veya Açıklama Yok)')}
                            </div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px; flex-shrink: 0;">
                        <label class="sam-switch">
                            <input type="checkbox" class="sam-ach-checkbox" data-id="${escapeSAMHtml(ach.id)}" ${isAchieved ? 'checked' : ''}>
                            <span class="sam-slider"></span>
                        </label>
                    </div>
                </div>
            `;
        }).join("");

        container.innerHTML = html;
    }

    function bindSAMModalEvents() {
        if (samModalEventsBound) return;
        samModalEventsBound = true;

        const modal = document.getElementById("modal-sam-achievements");
        const btnClose = document.getElementById("sam-modal-close-btn");
        const btnUnlockAll = document.getElementById("sam-btn-unlock-all");
        const btnLockAll = document.getElementById("sam-btn-lock-all");
        const btnInvert = document.getElementById("sam-btn-invert");
        const btnSave = document.getElementById("sam-btn-save-steam");
        const modalSearch = document.getElementById("sam-modal-search");
        const container = document.getElementById("sam-modal-achievements-container");

        const closeModal = () => {
            if (modal) modal.classList.remove("active");
        };

        if (btnClose) btnClose.addEventListener("click", closeModal);
        if (modal) {
            modal.addEventListener("click", (e) => {
                if (e.target === modal) closeModal();
            });
        }

        if (modalSearch) {
            modalSearch.addEventListener("input", () => {
                renderSAMAchievementsList(modalSearch.value);
            });
        }

        if (container) {
            container.addEventListener("click", (e) => {
                const item = e.target.closest(".sam-ach-item");
                if (!item) return;

                const id = item.getAttribute("data-id");
                if (!id) return;

                const ach = samCurrentAchievements.find(a => a.id === id);
                if (!ach) return;

                // Toggle state
                ach.achieved = !ach.achieved;

                // Sync UI
                const chk = item.querySelector(".sam-ach-checkbox");
                if (chk) chk.checked = ach.achieved;

                if (ach.achieved) {
                    item.classList.add("achieved");
                } else {
                    item.classList.remove("achieved");
                }

                const img = item.querySelector(".sam-ach-icon");
                if (img) {
                    const iconFile = ach.achieved ? (ach.icon || ach.icon_locked) : (ach.icon_locked || ach.icon);
                    if (iconFile) {
                        img.src = `https://cdn.steamstatic.com/steamcommunity/public/images/apps/${samCurrentAppId}/${iconFile}`;
                    }
                }

                updateSAMModalStats();
            });
        }

        if (btnUnlockAll) {
            btnUnlockAll.addEventListener("click", () => {
                samCurrentAchievements.forEach(a => a.achieved = true);
                renderSAMAchievementsList(modalSearch ? modalSearch.value : "");
                updateSAMModalStats();
            });
        }

        if (btnLockAll) {
            btnLockAll.addEventListener("click", () => {
                samCurrentAchievements.forEach(a => a.achieved = false);
                renderSAMAchievementsList(modalSearch ? modalSearch.value : "");
                updateSAMModalStats();
            });
        }

        if (btnInvert) {
            btnInvert.addEventListener("click", () => {
                samCurrentAchievements.forEach(a => a.achieved = !a.achieved);
                renderSAMAchievementsList(modalSearch ? modalSearch.value : "");
                updateSAMModalStats();
            });
        }

        if (btnSave) {
            btnSave.addEventListener("click", async () => {
                if (!samCurrentAppId) return;

                const originalHtml = btnSave.innerHTML;
                btnSave.disabled = true;
                btnSave.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Steam'e Kaydediliyor...`;

                try {
                    const unlockedIds = samCurrentAchievements.filter(a => a.achieved).map(a => a.id);
                    const resp = await fetch("/api/sam/save", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            appid: String(samCurrentAppId),
                            unlocked_ids: unlockedIds
                        })
                    });
                    const data = await resp.json();

                    if (data.success) {
                        if (window.showCustomAlert) {
                            window.showCustomAlert(
                                `Başarımlar Steam'e başarıyla aktarıldı!\n\nGüncellenen Başarım Sayısı: ${data.modified || 0}`,
                                "Steam'e Kaydedildi"
                            );
                        }
                    } else {
                        if (window.showCustomAlert) {
                            window.showCustomAlert(data.error || "Başarımlar kaydedilemedi.", "Kaydetme Hatası");
                        }
                    }
                } catch (err) {
                    console.error("Save error:", err);
                    if (window.showCustomAlert) {
                        window.showCustomAlert("Steam'e kaydetme sırasında hata oluştu: " + err.message, "Hata");
                    }
                } finally {
                    btnSave.disabled = false;
                    btnSave.innerHTML = originalHtml;
                }
            });
        }
    }

    async function openSAMAchievementsModal(appid, name = "", triggerBtn = null) {
        samCurrentAppId = String(appid);
        samCurrentAppName = name || `AppID ${appid}`;
        samCurrentAchievements = [];

        bindSAMModalEvents();

        const modal = document.getElementById("modal-sam-achievements");
        const titleEl = document.getElementById("sam-modal-game-name");
        const appidEl = document.getElementById("sam-modal-game-appid");
        const iconEl = document.getElementById("sam-modal-game-icon");
        const searchInput = document.getElementById("sam-modal-search");
        const container = document.getElementById("sam-modal-achievements-container");

        if (titleEl) titleEl.textContent = samCurrentAppName;
        if (appidEl) appidEl.textContent = `AppID: ${samCurrentAppId}`;
        if (searchInput) searchInput.value = "";

        if (iconEl) {
            iconEl.src = `/api/cover/${samCurrentAppId}`;
            iconEl.onerror = () => {
                iconEl.src = `https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/${samCurrentAppId}/header.jpg`;
            };
        }

        if (container) {
            container.innerHTML = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 260px; gap: 14px; color: #c084fc;">
                    <i class="fa-solid fa-circle-notch fa-spin fa-2x"></i>
                    <span style="font-size: 0.95rem; font-weight: 600;">Steam başarımları yükleniyor, lütfen bekleyin...</span>
                </div>
            `;
        }

        updateSAMModalStats();
        if (modal) modal.classList.add("active");

        try {
            const resp = await fetch(`/api/sam/achievements/${samCurrentAppId}`);
            const data = await resp.json();

            if (data.success && Array.isArray(data.achievements)) {
                samCurrentAchievements = data.achievements;
                renderSAMAchievementsList("");
                updateSAMModalStats();
            } else {
                if (container) {
                    container.innerHTML = `
                        <div style="text-align: center; padding: 50px 20px; color: #f87171;">
                            <i class="fa-solid fa-circle-exclamation fa-2x" style="margin-bottom: 12px; display: block;"></i>
                            <p style="font-size: 0.95rem; font-weight: 700; color: #fff;">Başarımlar Yüklenemedi</p>
                            <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 6px 0 16px;">${escapeSAMHtml(data.error || "Steam bağlantısı kurulamadı veya oyun kütüphanede doğrulanmadı.")}</p>
                            <button class="btn btn-secondary" onclick="window.launchSAMApp('${samCurrentAppId}', '${escapeSAMHtml(samCurrentAppName)}')" style="padding: 7px 18px; font-size: 0.85rem; cursor: pointer;">
                                <i class="fa-solid fa-rotate-right"></i> Yeniden Dene
                            </button>
                        </div>
                    `;
                }
            }
        } catch (err) {
            console.error("SAM achievements load error:", err);
            if (container) {
                container.innerHTML = `
                    <div style="text-align: center; padding: 50px 20px; color: #f87171;">
                        <i class="fa-solid fa-triangle-exclamation fa-2x" style="margin-bottom: 12px; display: block;"></i>
                        <p style="font-size: 0.95rem; font-weight: 700; color: #fff;">Bağlantı Hatası</p>
                        <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 6px 0 16px;">${escapeSAMHtml(err.message)}</p>
                    </div>
                `;
            }
        }
    }

    if (btnRefresh) {
        btnRefresh.addEventListener("click", () => {
            const icon = btnRefresh.querySelector("i");
            if (icon) icon.classList.add("fa-spin");
            loadSAMLibrary(true).finally(() => {
                if (icon) icon.classList.remove("fa-spin");
            });
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", () => {
            const q = searchInput.value.toLowerCase().trim();
            filterAndRenderSAMGames(q);
        });
    }

    window.launchSAMApp = openSAMAchievementsModal;
    window.loadSAMLibrary = loadSAMLibrary;

    // Immediately load games so they are ready as soon as the user opens the tab
    setTimeout(() => {
        try { loadSAMLibrary(false); } catch (e) {}
    }, 150);
}

async function loadSAMLibrary(force = false) {
    if (samLibraryLoaded && !force && samAllGames.length > 0) return;
    const grid = document.getElementById("sam-games-grid");
    const countEl = document.getElementById("sam-game-count");

    // 1. Immediately render cached games (0ms instant display)
    let initialGames = [];
    try {
        const cached = localStorage.getItem("steamrogue_sam_cache");
        if (cached) {
            const parsed = JSON.parse(cached);
            if (Array.isArray(parsed) && parsed.length > 0) {
                initialGames = parsed;
            }
        }
    } catch (e) {}

    if (initialGames.length === 0) {
        try {
            const libCached = localStorage.getItem("steamrogue_library_cache");
            if (libCached) {
                const parsedLib = JSON.parse(libCached);
                if (Array.isArray(parsedLib) && parsedLib.length > 0) {
                    initialGames = parsedLib;
                }
            }
        } catch (e) {}
    }

    if (initialGames.length === 0 && window.globalGameLibrary && Array.isArray(window.globalGameLibrary) && window.globalGameLibrary.length > 0) {
        initialGames = [...window.globalGameLibrary];
    }

    if (initialGames.length > 0 && samAllGames.length === 0) {
        samAllGames = initialGames;
        if (countEl) countEl.textContent = initialGames.length;
        const searchInput = document.getElementById("sam-search-input");
        const q = (searchInput && searchInput.value) ? String(searchInput.value).toLowerCase().trim() : "";
        filterAndRenderSAMGames(q);
    } else if (grid && (!samAllGames || samAllGames.length === 0)) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 45px 20px; color: var(--text-muted);">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2.2rem; color: #7c3aed; margin-bottom: 14px;"></i>
                <p style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary);">Kütüphaneniz taranıyor...</p>
                <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px;">Steam oyunlarınız ve başarımlar listeleniyor</p>
            </div>
        `;
    }

    // 2. Fetch fresh games list from backend (/api/sam/games)
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 12000);
        const resp = await fetch("/api/sam/games", { signal: controller.signal });
        clearTimeout(timeoutId);
        
        const data = await resp.json();
        let games = (data && data.games) || [];

        // If backend returned games, render them
        if (games.length > 0) {
            samAllGames = games;
            samLibraryLoaded = true;
            try {
                localStorage.setItem("steamrogue_sam_cache", JSON.stringify(games));
            } catch (e) {}

            if (countEl) countEl.textContent = games.length;
            const searchInput = document.getElementById("sam-search-input");
            const q = (searchInput && searchInput.value) ? String(searchInput.value).toLowerCase().trim() : "";
            filterAndRenderSAMGames(q);
            return;
        }
    } catch (err) {
        console.warn("Notice loading SAM games from network:", err);
    }

    // 3. Fallback: If samAllGames is still empty, fetch from /api/library
    if (!samAllGames || samAllGames.length === 0) {
        try {
            const libResp = await fetch("/api/library");
            const libData = await libResp.json();
            if (libData && libData.games && libData.games.length > 0) {
                samAllGames = libData.games;
                samLibraryLoaded = true;
                if (countEl) countEl.textContent = samAllGames.length;
                filterAndRenderSAMGames("");
                return;
            }
        } catch (e) {}
    }

    // 4. Final state if truly 0 games found
    if (!samAllGames || samAllGames.length === 0) {
        if (countEl) countEl.textContent = "0";
        if (grid) {
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 45px 20px; color: var(--text-muted);">
                    <i class="fa-solid fa-gamepad" style="font-size: 2.2rem; color: rgba(255,255,255,0.15); margin-bottom: 12px;"></i>
                    <p style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary);">Kütüphanenizde Henüz Oyun Bulunamadı</p>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 6px;">Steam hesabınıza giriş yapıldığından ve kütüphanenizde oyun bulunduğundan emin olun.</p>
                    <button class="btn btn-secondary" onclick="loadSAMLibrary(true)" style="margin-top: 14px; padding: 8px 18px; font-size: 0.85rem; cursor: pointer;">
                        <i class="fa-solid fa-rotate"></i> Kütüphaneyi Yeniden Tara
                    </button>
                </div>
            `;
        }
    }
}

function filterAndRenderSAMGames(query = "") {
    const grid = document.getElementById("sam-games-grid");
    const countEl = document.getElementById("sam-game-count");
    if (!grid) return;

    if (!samGridListenerBound) {
        samGridListenerBound = true;
        grid.addEventListener("click", (e) => {
            const btn = e.target.closest(".btn-sam-manage");
            if (btn) {
                const appid = btn.getAttribute("data-appid");
                const name = btn.getAttribute("data-name") || `AppID ${appid}`;
                if (typeof window.launchSAMApp === "function") {
                    window.launchSAMApp(appid, name, btn);
                }
            }
        });
    }

    let filtered = samAllGames || [];
    if (query) {
        filtered = samAllGames.filter(g => {
            const nameMatch = (g.name || "").toLowerCase().includes(query);
            const idMatch = String(g.appid || "").includes(query);
            return nameMatch || idMatch;
        });
    }

    if (countEl) countEl.textContent = filtered.length;

    if (!filtered || filtered.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 50px 20px; color: var(--text-muted);">
                <i class="fa-solid fa-magnifying-glass" style="font-size: 2.2rem; color: rgba(255,255,255,0.1); margin-bottom: 12px;"></i>
                <p style="font-size: 0.95rem; font-weight: 600; color: var(--text-secondary);">Eşleşen oyun bulunamadı</p>
                <p style="font-size: 0.8rem; margin-top: 4px;">Farklı bir arama yapmayı deneyin veya kütüphaneyi yenileyin.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = "";
    const fragment = document.createDocumentFragment();

    filtered.forEach(game => {
        const appid = String(game.appid);
        const name = game.name || `AppID ${appid}`;
        const card = document.createElement("div");
        card.className = "sam-game-card";

        const primaryCover = `/api/cover/${appid}`;
        const cdn1 = `https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps/${appid}/header.jpg`;
        const cdn2 = `https://cdn.cloudflare.steamstatic.com/steam/apps/${appid}/library_600x900.jpg`;

        card.innerHTML = `
            <div class="sam-card-img-wrapper">
                <img class="sam-card-img" src="${primaryCover}" alt="${name}" loading="lazy" decoding="async">
            </div>
            <div class="sam-card-body">
                <div>
                    <div class="sam-card-title" title="${name}">${name}</div>
                    <div class="sam-card-appid"><i class="fa-brands fa-steam"></i> AppID: ${appid}</div>
                </div>
                <button class="btn-sam-manage" data-appid="${appid}" data-name="${name.replace(/"/g, '&quot;')}" title="Bu oyun için Steam Achievement Manager'ı başlat">
                    <i class="fa-solid fa-trophy"></i> Başarımları Yönet
                </button>
            </div>
        `;

        const img = card.querySelector(".sam-card-img");
        if (img) {
            img.onerror = () => {
                if (!img.dataset.tried1) {
                    img.dataset.tried1 = "true";
                    img.src = cdn1;
                } else if (!img.dataset.tried2) {
                    img.dataset.tried2 = "true";
                    img.src = cdn2;
                } else {
                    img.style.display = "none";
                }
            };
        }

        fragment.appendChild(card);
    });

    grid.appendChild(fragment);
}

