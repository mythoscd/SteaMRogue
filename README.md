<div align="center">

# 🎮 SteaMRogue
### The All-in-One Modern Steam Library Companion, OnlineFix Multiplayer & Toolkit

[![Version](https://img.shields.io/badge/Version-v1.2.0-7c3aed?style=for-the-badge&logo=github)](https://github.com/mythoscd/SteaMRogue/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20(x64)-0078D6?style=for-the-badge&logo=windows)](https://github.com/mythoscd/SteaMRogue/releases/latest)
[![Stack](https://img.shields.io/badge/Stack-Electron%20%2B%20Python%203.14-success?style=for-the-badge)](https://github.com/mythoscd/SteaMRogue)
[![Language](https://img.shields.io/badge/Languages-English%20%7C%20T%C3%BCrk%C3%A7e-informational?style=for-the-badge)](https://github.com/mythoscd/SteaMRogue)
[![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

<p align="center">
  <b>SteaMRogue</b> is a next-generation desktop application engineered to enrich and simplify your Steam experience. It empowers users with one-click library expansion, native Steam disk selection, automated OnlineFix multiplayer patches, integrated Steam Achievement Management (SAM), live discount tracking, and instant dual-language switching with zero friction.
</p>

[🚀 Quick Start](#-quick-start--installation) • [🌍 Multilingual Experience](#-multilingual-experience-v120) • [🛡️ Operational Modes](#️-operational-modes-safe-mode-vs-steamrogue) • [✨ Key Features](#-key-features) • [🛠️ Architecture](#️-architecture) • [❓ FAQ](#-frequently-asked-questions) • [📦 Releases](https://github.com/mythoscd/SteaMRogue/releases)

---

</div>

## 🚀 Quick Start & Installation

SteaMRogue is delivered as a self-contained, single-click Windows installer (NSIS). It requires no administrative UAC elevation and installs directly to your local user directory.

### 📥 1. Download
Get the latest stable release directly:
* ⬇️ **[SteaMRogue-Setup-1.2.0.exe (Direct Download)](https://github.com/mythoscd/SteaMRogue/releases/download/v1.2.0/SteaMRogue-Setup-1.2.0.exe)**
* 📋 All past and current releases: **[GitHub Releases](https://github.com/mythoscd/SteaMRogue/releases)**

### ⚡ 2. Setup
1. Run `SteaMRogue-Setup-1.2.0.exe`.
2. Installation finishes automatically in seconds, creating a **SteaMRogue** shortcut on your desktop.
3. Upon launch, SteaMRogue automatically recognizes your Steam installation, verifies component integrity, and is immediately ready to go.

> [!TIP]
> **Built-in Auto-Update:**  
> Once installed, you never need to manually fetch new builds. SteaMRogue quietly checks for releases via GitHub and notifies you when an update is ready to install with a single click.

---

## 🌍 Multilingual Experience (v1.2.0)

SteaMRogue now features first-class internationalization with complete coverage across the entire platform:
* **Interactive Language Selector:** Switch effortlessly between **English** 🇬🇧 and **Türkçe** 🇹🇷 using the stylish flag button in the top navigation bar.
* **Persistent Preferences:** Your language choice is saved permanently (`localStorage` + config) across restarts.
* **Seamless Transition:** Language changes take effect immediately without requiring an application restart. A sleek visual transition screen smoothly refreshes all UI components.
* **100% Comprehensive Translation:** Every tab, modal dialogue, tooltip, context menu, and dynamic notification is localized with care.

---

## 🛡️ Operational Modes: Safe Mode vs. SteaMRogue

SteaMRogue offers dual operational states designed around your comfort and gaming routine:

| Mode | What It Does | Best For |
|---|---|---|
| **🛡️ Safe Mode** | Completely stops background injection engines and restores Steam to a 100% clean, vanilla state. All games already in your library remain fully playable and preserved. | Playing VAC-secured competitive games (e.g., *Counter-Strike 2*, *Dota 2*, *TF2*). |
| **⚡ SteaMRogue Mode** | Activates the library management and injection engine, allowing one-click game additions, manifest syncing, and DLC integration. | Expanding your library, queuing game downloads, and applying patches. |

Switch between modes at any time with a single click from the top header toggle or directly from the Windows system tray icon right-click menu.

---

## ✨ Key Features

### 🎮 1. Smart Library Grid & 20-Game Pagination
* **Balanced 20-Card Layout:** Enjoy an aesthetic, responsive grid displaying 10 top and 10 bottom game posters per page.
* **Dynamic Pagination:** Effortlessly browse larger libraries with intuitive `Previous` / `Next` controls and real-time page indicators.
* **Universal Search & Add:** Add titles using **AppID**, **Game Name**, or raw **Steam Store URLs** (`store.steampowered.com/app/...`).
* **Native Steam Drive Selection:** Install games to any drive (C:, D:, or external SSDs) using Steam's official installation prompt—no forced drive configurations.
* **One-Click Safe Steam Restart:** Apply library updates cleanly with a single button that restarts Steam without hung background processes.

### 🏆 2. Integrated Steam Achievement Manager (SAM)
* **Native Cyberpunk UI:** Manage your Steam achievements directly inside SteaMRogue without launching external legacy utilities.
* **Full Control:** Inspect achievements, view completion percentages, lock or unlock individual milestones, invert selections, or batch toggle all achievements with instant Steam sync.

### 🌐 3. OnlineFix Multiplayer Integration
* **Instant Patch Discovery:** Automatically queries OnlineFix databases for games in your library or search queue.
* **Automated Installation:** Download, extract (handling default archive passwords), and integrate multiplayer files directly into your game folder with zero manual hassle.

### ⚡ 4. Bypass & Fix Engine
* **Single-Player Fix Deployment:** Choose between intelligent automatic directory detection across all your Steam libraries or manual folder selection.
* **Built-in Exclusions:** Step-by-step guidance to prevent common false positives from security software.

### 🏷️ 5. Real-Time Deals & Discounts Radar
* **Live Steam Discount Feed:** Scans Steam store promotions in real time.
* **Filter by Preference:** Filter deals by genre (Action, RPG, Strategy, Indie, etc.), discount percentage (up to 90%+ off), and price caps.

### 🛠️ 6. System Health Diagnostics & Self-Healing
* **Automatic Startup Audit:** Detects and remedies hung registry locks, dead PID artifacts, and corrupted Steam crash states.
* **Lua BOM Cleaner:** Automatically purges hidden UTF-8 BOM characters from community scripts, preventing Steam syntax crash issues.
* **Visual C++ Runtime Verification:** Scans for both 32-bit and 64-bit VC++ redistributable packages and installs any missing libraries silently from official sources.

---

## 🛠️ Architecture

SteaMRogue combines modern web front-end technologies with Python's data-processing power:

```
┌────────────────────────────────────────────────────────┐
│                   SteaMRogue UI                        │
│         Electron 33 • HTML5 • Modern CSS • Vanilla JS  │
└──────────────────────────┬─────────────────────────────┘
                           │ IPC / REST API (Port 5000)
┌──────────────────────────▼─────────────────────────────┐
│                 Python Backend Engine                  │
│    Flask API • Manifest & Steam Store Parser • SQLite  │
└──────────────────────────┬─────────────────────────────┘
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
┌──────────────┐                       ┌──────────────┐
│ Steam Client │                       │  OnlineFix   │
│  (Hook/DLL)  │                       │ (Multiplayer)│
└──────────────┘                       └──────────────┘
```

| Component | Technology | Description |
|---|---|---|
| **User Interface** | Electron 33, HTML5, CSS3, JavaScript | Cyberpunk purple/neon aesthetic with fluid animations |
| **Backend Core** | Python 3.14 (Flask, PyInstaller) | Manifest resolution, Steam Store integration, system file manager |
| **Achievement Module** | .NET / C# SAMWorker & SteamWorks API | Native achievement query and modification bridge |
| **Internationalization** | Custom i18n Engine | Client-side reactive dictionaries for English and Turkish |
| **Auto-Updater** | Electron Updater & GitHub Releases | Smart version tracking, delta repair, and automated installation |

---

## 📋 System Requirements

| Requirement | Specification |
|---|---|
| **Operating System** | Windows 10 / Windows 11 (64-bit) |
| **Architecture** | x64-compatible processor |
| **Steam Client** | Official Steam desktop client installed |
| **Privileges** | Standard user privileges (No Administrator/UAC required) |
| **Disk Space** | ~180 MB for application files |
| **Network** | Active internet connection for updates, manifests, and patches |

---

## ❓ Frequently Asked Questions

<details>
<summary><b>1. A game was added, but Steam shows "No licenses" or download won't start?</b></summary>
<br>

This happens when Steam retains cached download state. To resolve:
1. Open the **Settings** tab in SteaMRogue.
2. Click **"Clear Download Cache"** under the SteamTools card.
3. Steam will restart with fresh cache and the download will proceed normally.
</details>

<details>
<summary><b>2. How do I play multiplayer with friends via OnlineFix?</b></summary>
<br>

1. Both you and your friend should have the title added to your Steam libraries.
2. Download and apply the corresponding **OnlineFix patch** through SteaMRogue.
3. Launch the game from Steam and invite your friend using the standard Steam overlay (**Shift + Tab**).
</details>

<details>
<summary><b>3. Why might security software flag certain files?</b></summary>
<br>

Multiplayer integration files and custom DLL wrappers redirect specific game functions to enable features, which can sometimes trigger false-positive heuristics. You can use the built-in **"Add Defender Exclusion"** button to safely whitelist your folders or use **"Restore from Quarantine"** if needed.
</details>

<details>
<summary><b>4. How do I switch languages?</b></summary>
<br>

Click the round flag button next to the window control icons in the top bar. Choose **English** or **Türkçe** from the dropdown menu. The interface will switch immediately and remember your choice.
</details>

---

## 🤝 Contributing & Feedback

SteaMRogue is an open project welcoming community suggestions, bug reports, and pull requests.

* 🐛 Found a bug? Open an issue on [GitHub Issues](https://github.com/mythoscd/SteaMRogue/issues).
* 💡 Have a feature idea? Start a discussion or submit a Pull Request.
* ⭐ If you enjoy using SteaMRogue, please leave a star on the repository!

---

<div align="center">

🎮 **Your library, your control.**  
Crafted with ❤️ by [mythoscd](https://github.com/mythoscd)

</div>