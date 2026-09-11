<div align="center">

# 🎮 SteaMRogue
### Hepsi Bir Arada Steam Kütüphane Yöneticisi & Multiplayer Yama Platformu

[![Sürüm](https://img.shields.io/badge/S%C3%BCr%C3%BCm-v1.0.6-7c3aed?style=for-the-badge)](https://github.com/mythoscd/SteaMRogue/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue?style=for-the-badge&logo=windows)](https://github.com/mythoscd/SteaMRogue/releases)
[![Durum](https://img.shields.io/badge/Durum-Aktif%20%26%20G%C3%BCncel-brightgreen?style=for-the-badge)](https://github.com/mythoscd/SteaMRogue)
[![Otomatik Güncelleme](https://img.shields.io/badge/Otomatik%20G%C3%BCncelleme-Aktif-orange?style=for-the-badge&logo=github)](https://github.com/mythoscd/SteaMRogue)

<p align="center">
  Steam kütüphanenizi yönetin, oyunları orijinal lisanslı gibi ekleyin, çok oyunculu (OnlineFix) yamalarını tek tıkla kurun ve indirimleri takip edin — hepsi tek bir modern masaüstü uygulamasında.
</p>

[🚀 Genel Bakış](#-genel-bakış) • [✨ Özellikler](#-özellikler) • [🛠️ Teknoloji Altyapısı](#️-teknoloji-altyapısı) • [📋 Sistem Gereksinimleri](#-sistem-gereksinimleri) • [📦 Kurulum](#-kurulum) • [❓ SSS](#-sıkça-sorulan-sorular)

---

</div>

## 🚀 Genel Bakış

**SteaMRogue**, oyuncuların ihtiyaç duyduğu her şeyi tek çatı altında toplayan modern bir oyun ve kütüphane platformudur.

Steam kütüphanenize doğrudan oyun entegre edin, kilitleri açın, çok oyunculu oyunlar için OnlineFix yamalarını otomatik indirip kurun ve Steam indirimlerini kaçırmayın.

Proje 3 temel ilke üzerine inşa edilmiştir:
* ⚡ **Hızlı:** Hafif ve akıcı mimari, anında tepki süresi.
* 🎮 **Basit:** Karışık dosya kopyalama işleri yok, her şey tek tıkla.
* 💚 **Tamamen Ücretsiz:** Reklamsız, aboneliksiz, oyuncular için bağımsız ekosistem.

---

## ✨ Özellikler

### 🎮 Steam Kütüphane Entegrasyonu
* **Orijinal Disk Seçimi:** Sahte ACF dosyalarıyla diskinizi C: sürücüsüne zorlamaz; oyunu kurarken Steam'in kendi kurulum penceresinden istediğiniz diski (C, D veya harici SSD) seçebilirsiniz.
* **Otomatik Manifest & Lua Yönetimi:** Topluluk veritabanlarından (ProjectLightning, SPIN0ZAi, ManifestHub vb.) en güncel manifestleri otomatik çeker ve Steam'e işler.
* **Canlı Kapak & Görsel Senkronizasyonu:** Oyun kütüphaneniz için yüksek çözünürlüklü kapak görselleri doğrudan Steam CDN üzerinden otomatik çekilir.
* **Tek Tıkla Steam Yeniden Başlatıcı:** Steam istemcisini hiçbir onay kutusuyla uğraştırmadan tek tıkla kapatıp açar.

### 🌐 OnlineFix Çok Oyunculu (Multiplayer) Desteği
* Kütüphanenizdeki veya aradığınız herhangi bir oyun için OnlineFix veritabanında anında yama taraması yapar.
* **Gelişmiş İndirme Desteği:**
  * ⚡ **Pixeldrain:** Yüksek hızlı doğrudan indirme.
  * 🚀 **Gofile:** Otomatik token ve salt çözücü ile kesintisiz indirme.
  * 🛡️ **FileDitch & Alternatif Sunucular**
* **Otomatik Entegrasyon:** İndirilen yamayı otomatik olarak açar ve oyun dizinine kurar; dosyaları elle taşımakla uğraşmazsınız.

### 🛠️ Yerleşik Araçlar & Güvenlik
* **SteamTools Motoru:** En güncel SteamTools DLL bileşenlerini (`dwmapi.dll`, `xinput1_4.dll`, `OpenSteamTool.dll`) otomatik denetler ve entegre eder.
* **Windows Defender Asistanı:** Yanlış virüs uyarılarını (false-positive) önlemek için Steam ve SteaMRogue klasörlerini tek tıkla Windows Güvenliği İstisnalarına ekler.
* **Yerleşik Otomatik Güncelleme:** Yeni bir sürüm çıktığında uygulama içinde bildirim verir ve tek tıkla kendisini en güncel sürüme yükseltir.

---

## 🛠️ Teknoloji Altyapısı

| Bileşen | Kullanılan Teknoloji |
|---|---|
| **Arayüz (Frontend)** | Electron, HTML5, CSS3, Modern Vanilla JavaScript |
| **Arka Plan (Backend)** | Python 3.14 (Flask API, PyInstaller) |
| **Veritabanı & Önbellek** | SQLite3 / Yerel JSON Cache |
| **İndirme & Arşiv Motoru** | Requests, Özel Çözücüler, Native Zip & UnRAR |
| **Dağıtım & Paketleme** | NSIS Installer, GitHub Releases |

---

## 📋 Sistem Gereksinimleri

| Gereksinim | Windows |
|---|---|
| **İşletim Sistemi** | Windows 10 / 11 (64-bit) |
| **Mimari** | x64 |
| **Steam İstemcisi** | Kurulu olmalıdır |
| **Yönetici Yetkisi** | Kurulum için gerekmez (`%localappdata%`) |
| **Disk Alanı** | ~150 MB (Uygulama) + İndirmeler |
| **İnternet Bağlantısı** | Manifestler ve yama indirmeleri için gereklidir |

---

## 📦 Kurulum

### 💻 Windows Kurulumu
1. **[Releases](https://github.com/mythoscd/SteaMRogue/releases/latest)** sayfasına gidin.
2. En son `SteaMRogue-Setup-1.x.x.exe` dosyasını indirin.
3. İndirdiğiniz dosyaya çift tıklayın. Kurulum tamamen sessiz ve otomatiktir; saniyeler içinde masaüstünüze **SteaMRogue** kısayolu eklenecektir.
4. Uygulama otomatik olarak `%localappdata%\Programs\steamtools-auto` dizinine kurulur, yönetici yetkisi istemez.

> [!TIP]
> SteaMRogue yerleşik otomatik güncelleme motoruna sahiptir. Kurulumu bir kez yaptıktan sonra gelecekteki tüm yeni sürümler uygulama içinden tek tıkla otomatik olarak alınır.

---

## ❓ Sıkça Sorulan Sorular

<details>
<summary><b>1. Oyun yüklerken neden internet bağlantısı yok hatası alıyorum?</b></summary>
Steam açıkken manifest eklendiğinde istemci henüz dosyaları hafızaya almamış olabilir. SteaMRogue arayüzündeki <b>Steam'i Yeniden Başlat</b> butonuna basarak Steam'i tazeleyin ve indirmeyi tekrar başlatın.
</details>

<details>
<summary><b>2. İndirdiğim OnlineFix yamaları güvenli mi?</b></summary>
Tüm yamalar doğrudan resmi OnlineFix kaynaklarından çekilir. Bazı antivirüs yazılımları çok oyunculu crack ve DLL dosyalarını yanlış pozitif (false-positive) olarak algılayabilir. Bu durumda arayüzdeki "Dışlamayı Uygula" özelliğini kullanabilirsiniz.
</details>

<details>
<summary><b>3. İstediğim diske oyun kurabilir miyim?</b></summary>
Evet! SteaMRogue diskinizi zorla C: sürücüsüne kilitlemez. Steam'in orijinal yükleme penceresi açılır ve Steam'de tanımlı olan dilediğiniz sürücüyü (C:, D:, harici SSD) özgürce seçebilirsiniz.
</details>

---

<div align="center">

🎮 **SteaMRogue** — Kütüphanen, senin kuralların.  
*Tek uygulama, sınırsız oyun özgürlüğü.*

</div>