<div align="center">

# 🎮 SteaMRogue
### Next-Gen Steam Library, Game Unlocking & Multiplayer Patch Manager

[![Release](https://img.shields.io/github/v/release/mythoscd/SteaMRogue?style=for-the-badge&color=7c3aed&label=Version)](https://github.com/mythoscd/SteaMRogue/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue?style=for-the-badge&logo=windows)](https://github.com/mythoscd/SteaMRogue/releases)
[![Status](https://img.shields.io/badge/Status-Active%20%26%20Maintained-brightgreen?style=for-the-badge)](https://github.com/mythoscd/SteaMRogue)
[![Auto Update](https://img.shields.io/badge/Auto%20Update-Enabled-orange?style=for-the-badge&logo=github)](https://github.com/mythoscd/SteaMRogue)

<p align="center">
  <b>SteaMRogue</b> is a modern, high-performance desktop application designed to give gamers complete control over their Steam library. Powered by SteamTools, featuring automated OnlineFix multiplayer patch integration, native Steam drive selection, and a built-in auto-update engine.
</p>

[📥 Download Latest Release (v1.0.1)](https://github.com/mythoscd/SteaMRogue/releases/latest) • [✨ Features](#-features) • [🚀 Installation](#-installation) • [📖 Guide](#-user-guide) • [❓ FAQ](#-frequently-asked-questions)

---

</div>

## 🌟 Features

### 1. 🎯 Native Steam Library & Drive Selection
* Added games appear directly in your official Steam client library as owned titles.
* **No forced drive locks:** SteaMRogue preserves Steam's native installation prompt.
* Choose your preferred installation drive (**C:**, **D:**, NVMe, or external SSD) directly within Steam's official UI.
* Eliminates "Not Enough Disk Space" errors caused by pre-assigned drive manifests.

### 2. 🌐 OnlineFix & Multiplayer Patch Engine
* Instantly search and download OnlineFix multiplayer patches for supported titles directly within the application.
* **Multi-Host Fast Download Pipeline:**
  * ⚡ **Pixeldrain API** (High-speed direct downloading)
  * 🚀 **Gofile Integration** (Automated token and salt negotiation)
  * 🛡️ **FileDitch & Mirror Fallbacks**
* **1-Click Auto-Integration:** Automatically unpacks password-protected archives (e.g. `online-fix.me`), installs patch files directly into the game's directory, and cleans up temporary archives.

### 3. 🚀 Built-in Auto-Update Engine
* Automatically checks for new versions on launch via GitHub Releases.
* When an update is published, a sleek non-intrusive notification card appears in the bottom-right corner.
* Downloads updates silently in the background and applies them with a single click (**"Restart & Update"**). No manual installer downloads needed!

### 4. 🛡️ Antivirus & Defender Helper
* Eliminates false-positive detections commonly triggered by game-hooking DLLs (SteamTools / SmokeAPI / OnlineFix).
* Features a built-in shortcut to quickly whitelist Steam directories in Windows Defender.

### 5. 🎨 Modern Dark Neon Interface
* Sleek dark-mode aesthetic inspired by Project Lightning with purple and neon accents.
* Library game cover art, real-time download progress meters, and responsive UI controls.

---

## 📥 Installation

1. Navigate to the **[Releases](https://github.com/mythoscd/SteaMRogue/releases/latest)** page.
2. Download `SteaMRogue Setup X.X.X.exe`.
3. Run the installer. Setup is completely automated and will create a desktop shortcut within seconds.
4. Launch SteaMRogue and start managing your library!

> [!NOTE]
> Because SteaMRogue has a built-in auto-updater, manual installation is only required **once**. All future updates will be applied automatically inside the application.

---

## 📖 User Guide

### 🎮 Adding a New Game
1. Launch SteaMRogue and enter the game title or Steam AppID into the search bar.
2. Select the game from the search results and click **"Add to Library"**.
3. Once completed, restart your Steam client.
4. Locate the game in your Steam Library and click the blue **"INSTALL"** button.
5. In the native Steam installation window, select your desired installation drive (C:, D:, etc.) and proceed!

### 🌐 Applying a Multiplayer (OnlineFix) Patch
1. Navigate to the **"OnlineFix"** section inside SteaMRogue.
2. Search for the title you wish to play multiplayer.
3. Click **"Download Patch"** and choose **"Integrate into Game"**.
4. The system will download the patch, extract it, and copy all required files into the game folder automatically.
5. Launch the game and enjoy multiplayer with friends!

---

## ❓ Frequently Asked Questions

<details>
<summary><b>1. Can I choose which drive to install games on?</b></summary>
<br>
<b>Yes!</b> SteaMRogue does not force or lock games onto any specific drive. It triggers Steam's native installation dialog so you can choose Windows 11 (C:), Secondary Volume (D:), or any other library drive directly in Steam.
</details>

<details>
<summary><b>2. How do updates work?</b></summary>
<br>
Completely automatically! When a new version is released, SteaMRogue will notify you in the bottom-right corner and download the update in the background. Simply click <i>"Restart & Update"</i> when prompted.
</details>

<details>
<summary><b>3. What should I do if Windows Defender or Antivirus flags a file?</b></summary>
<br>
Game unlockers and multiplayer fix DLLs often trigger "False Positive" alerts because they hook into game executables. You can use the <b>"Add Exclusion"</b> button in SteaMRogue settings to whitelist your Steam directory.
</details>

<details>
<summary><b>4. Do I need to enter OnlineFix passwords manually?</b></summary>
<br>
No. SteaMRogue's built-in extraction routine automatically decrypts and unpacks archives using standard OnlineFix passwords (such as <code>online-fix.me</code>).
</details>

---

## 💻 System Requirements

| Component | Minimum Requirements | Recommended |
| :--- | :--- | :--- |
| **OS** | Windows 10 (64-bit) | Windows 11 (64-bit) |
| **Processor** | Dual-core 1.8 GHz | Quad-core 2.5 GHz or higher |
| **Memory (RAM)** | 2 GB RAM | 4 GB RAM or higher |
| **Storage** | 250 MB free space | SSD Storage |
| **Steam** | Updated Steam Client | Updated Steam Client |

---

<div align="center">

Maintained & Developed by **[@mythoscd](https://github.com/mythoscd)**  
*SteaMRogue Project — All rights reserved.*

</div>
