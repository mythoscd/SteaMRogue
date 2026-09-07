<div align="center">
  <img src="icon.png" width="96" height="96" alt="SteaMRogue" />
  <h1>SteaMRogue</h1>
  <p>Steam library manager with SteamTools unlocker and automated OnlineFix multiplayer patches.</p>

  <a href="https://github.com/mythoscd/SteaMRogue/releases/latest">
    <img src="https://img.shields.io/github/v/release/mythoscd/SteaMRogue?style=flat&color=6d28d9" alt="Latest Release">
  </a>
  <img src="https://img.shields.io/badge/platform-Windows-blue?style=flat" alt="Platform">
</div>

---

SteaMRogue is a lightweight desktop app that makes managing unlocked Steam games and multiplayer fixes painless. Instead of manually moving lua files, editing manifests, or dealing with link shorteners to grab OnlineFix patches, SteaMRogue handles everything from a clean interface.

## Features

- **Steam drive selection:** Unlike older tools that force games into `C:\` and cause "not enough disk space" errors, SteaMRogue lets Steam show its native install dialog so you can pick any drive you want (C:, D:, NVMe, etc.).
- **OnlineFix downloader:** Searches OnlineFix directly, downloads through Pixeldrain, Gofile, or FileDitch mirrors, decrypts the zip/rar, and extracts the files straight into the game folder.
- **Built-in auto-updates:** When a new update is pushed, the app downloads it in the background and prompts you to restart. You don't have to re-download setup files manually.
- **Antivirus helper:** Includes a one-click button to add your Steam folder to Windows Defender exclusions so false-positives don't delete your files.
- **Clean dark UI:** Simple, distraction-free interface built with Electron and Python.

## Installation

1. Download the latest installer from [Releases](https://github.com/mythoscd/SteaMRogue/releases/latest) (`SteaMRogue Setup 1.0.1.exe`).
2. Run the setup. It will install silently and add a shortcut to your desktop.
3. You're done. Future updates will download automatically inside the app.

## How to use

### Adding a game to Steam
1. Search for the game name or AppID in SteaMRogue.
2. Click **Add to Library**.
3. Restart Steam.
4. Find the game in your Steam library, click **Install**, and choose your drive as usual.

### Installing multiplayer fixes (OnlineFix)
1. Head over to the **OnlineFix** tab in the app.
2. Search for the game you want to play.
3. Click **Download** and select **Integrate into Game**.
4. SteaMRogue downloads the patch, extracts it with the password, and places the files inside the game's directory.

## FAQ

**Can I install games on another drive like D:?**  
Yes. SteaMRogue doesn't lock the game path on disk, so Steam's native "Install to:" prompt will show up allowing you to select any configured library folder.

**Do my friends need to download new versions manually?**  
No. As long as they install v1.0.1 once, any future update will pop up in the corner of their app and update with a single click.

**Why does my antivirus flag the files?**  
Game unlockers and multiplayer fix DLLs hook into game memory to route connections through Steam Spacewar (AppID 480). Antiviruses often flag these as generic hacktools or false positives. You can use the exclusion button in settings to whitelist the folder.

**Do I need to extract archives or type the online-fix.me password?**  
No, SteaMRogue handles the extraction and password automatically.

---

### Credits
Made by [mythoscd](https://github.com/mythoscd).
