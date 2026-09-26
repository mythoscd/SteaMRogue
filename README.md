<div align="center">

# 🎮 SteaMRogue
### Hepsi Bir Arada Steam Kütüphane Yöneticisi, OnlineFix Multiplayer & Otomatik Güncelleme Platformu

[![Sürüm](https://img.shields.io/badge/S%C3%BCr%C3%BCm-v1.1.2-7c3aed?style=for-the-badge&logo=github)](https://github.com/mythoscd/SteaMRogue/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20(x64)-0078D6?style=for-the-badge&logo=windows)](https://github.com/mythoscd/SteaMRogue/releases/latest)
[![Teknoloji](https://img.shields.io/badge/Mimari-Electron%20%2B%20Python%203.14-success?style=for-the-badge)](https://github.com/mythoscd/SteaMRogue)
[![Otomatik Güncelleme](https://img.shields.io/badge/Otomatik%20G%C3%BCncelleme-Aktif%20(In--App)-orange?style=for-the-badge&logo=electron)](https://github.com/mythoscd/SteaMRogue)
[![Lisans](https://img.shields.io/badge/Lisans-MIT-informational?style=for-the-badge)](LICENSE)

<p align="center">
  <b>SteaMRogue</b>, Steam kütüphanenizi tek tıkla zenginleştiren, oyunları orijinal disk seçim penceresiyle entegre eden, çok oyunculu (OnlineFix) yamalarını otomatik indirip kuran ve yerleşik güncelleme motoruyla daima en son sürümde kalan yeni nesil masaüstü platformudur.
</p>

[🚀 Hızlı Başlangıç](#-hızlı-başlangıç--kurulum) • [✨ Öne Çıkan Özellikler](#-öne-çıkan-özellikler) • [🛠️ Teknoloji Mimarisi](#️-teknoloji-mimarisi) • [❓ Sıkça Sorulan Sorular (SSS)](#-sıkça-sorulan-sorular-sss) • [📦 Sürümler](https://github.com/mythoscd/SteaMRogue/releases)

---

</div>

## 🚀 Hızlı Başlangıç & Kurulum

SteaMRogue, bağımsız tek tık kurulum yürütücüsü (NSIS) ile birlikte gelir. Yönetici (UAC) yetkisi gerektirmez ve doğrudan kullanıcı dizinine kurulur.

### 📥 1. İndirme
En son kararlı sürümü doğrudan aşağıdaki bağlantıdan edinebilirsiniz:
* ⬇️ **[SteaMRogue-Setup-1.1.2.exe (Doğrudan İndir)](https://github.com/mythoscd/SteaMRogue/releases/download/v1.1.2/SteaMRogue-Setup-1.1.2.exe)**
* 📋 Tüm geçmiş ve güncel sürümler için: **[GitHub Releases](https://github.com/mythoscd/SteaMRogue/releases)**

### ⚡ 2. Kurulum
1. İndirdiğiniz `SteaMRogue-Setup-1.1.2.exe` dosyasını çalıştırın.
2. Kurulum otomatik olarak tamamlanır ve masaüstünüze **SteaMRogue** kısayolu eklenir.
3. Uygulama açıldığında Steam istemcinizi otomatik olarak algılar ve kullanıma hazır hale gelir.

> [!TIP]
> **Yerleşik Otomatik Güncelleme (In-App Auto-Update):**  
> Kurulumu bir kez yaptıktan sonra manuel olarak yeni sürüm aramanıza gerek yoktur. SteaMRogue her açılışta güncellemeleri arka planda denetler ve yeni bir sürüm çıktığında tek tıkla kendisini günceller.

---

## ✨ Öne Çıkan Özellikler

### 🎮 1. Akıllı Steam Kütüphane Entegrasyonu
* **Çok Yönlü Arama & Ekleme:** Sayısal **AppID**, doğrudan **Oyun Adı** veya tarayıcınızdan kopyaladığınız **Steam Mağaza Linkleri** (`store.steampowered.com/app/...`) ile anında oyun arayıp ekleyin.
* **Yaş Kısıtlamalı & Yetişkin İçerik Desteği:** Steam Store API üzerindeki yaş doğrulamalı (*Cyberpunk 2077*, *Ready or Not*, *GTA V* vb.) veya paket yönlendirmeli (*Counter-Strike 2*, *Terraria* vb.) tüm oyunların kapak resimleri ve meta verileri eksiksiz işlenir.
* **Serbest Disk Seçimi:** Sahte ACF yapılandırmalarıyla sisteminizi C: sürücüsüne zorlamaz; oyunu kurarken Steam'in kendi kurulum penceresinden istediğiniz diski (C, D veya harici SSD) seçebilirsiniz.
* **Otomatik Manifest & Lua Yönetimi:** Topluluk veritabanlarından (ProjectLightning, SPIN0ZAi, ManifestHub vb.) en güncel manifestleri otomatik çeker ve kütüphanenize işler.
* **Çevrimdışı Kanca & İmza Motoru:** OpenSteamTool `.toml` imza dosyaları kurulum paketine tam gömülüdür; sıfır kurulumlarda veya ağ kısıtlamalarında kanca sorunsuz çalışır.
* **Tek Tıkla Steam Yeniden Başlatıcı:** Kütüphane değişikliklerinin anında geçerli olması için Steam istemcisini arka plan kilitlenmelerine yol açmadan tek tıkla güvenle yeniden başlatır.

### 🌐 2. OnlineFix Çok Oyunculu (Multiplayer) Desteği
* **Doğrudan Veritabanı Taraması:** Kütüphanenizdeki veya aradığınız herhangi bir oyun için OnlineFix altyapısında anında çok oyunculu yama taraması yapar.
* **Yüksek Hızlı İndiriciler:**
  * ⚡ **Pixeldrain:** Yüksek hızlı doğrudan indirme motoru.
  * 🚀 **Gofile:** Otomatik token ve sunucu çözücü ile kesintisiz indirme.
  * 🛡️ **FileDitch & Alternatif Aynalar:** Kesintisiz yedek indirme hatları.
* **Otomatik Kurulum & Entegrasyon:** İndirilen çok oyunculu yamaları otomatik arşivden çıkarır ve oyun dizinine uygular.

### 🛡️ 3. Güvenlik & Sistem Uyumluluğu
* **SteamTools Entegrasyonu:** En güncel SteamTools DLL bileşenlerini (`OpenSteamTool.dll`, `dwmapi.dll`, `xinput1_4.dll`) otomatik denetler ve entegre eder.
* **Windows Defender Asistanı:** Çok oyunculu crack ve kanca dosyalarının antivirüs tarafından yanlış pozitif (false-positive) olarak engellenmesini önlemek için tek tıkla Windows Defender İstisnası oluşturur.
* **Hafif ve Kararlı:** Minimum CPU ve RAM kullanımıyla sisteminizi yormadan arka planda veya ön planda akıcı çalışır.

### 🔄 4. Hibrit Otomatik Güncelleme & Onarım Sistemi
* **Kesintisiz Arka Plan Taraması:** Uygulama açılışında yeni sürümler otomatik olarak denetlenir ve arka planda güvenle indirilir.
* **Akıllı Tarih & Hash Algılama:** Sürüm numarası artırılmasa bile (`1.1.2 == 1.1.2`), GitHub üzerindeki en son yayın tarihi ve SHA-512 dosya imzası taranarak en güncel düzeltmeler anında algılanır.
* **Tek Tıkla Güncelleme & Onarım:** Ayarlar sekmesinde bulunan **"Güncellemeleri Denetle"** ile anlık durum sorgulaması yapabilir, **"Son Sürümü Yeniden İndir / Onar"** butonu ile olası bozulmalarda en son sürüm kurulum paketini tek tıkla temiz olarak kurabilirsiniz.
* **Tam Dinamik Sürüm Senkronizasyonu:** Arayüzdeki tüm sürüm etiketleri doğrudan Electron çekirdeğinden dinamik beslenir; eski yazı kalması tamamen engellenmiştir.

---

## 🛠️ Teknoloji Mimarisi

SteaMRogue, masaüstü deneyimini modern web teknolojilerinin esnekliği ve Python'ın veri işleme gücüyle birleştirir:

```
┌────────────────────────────────────────────────────────┐
│                   SteaMRogue UI                        │
│         Electron 33 • HTML5 • Modern CSS • JS          │
└──────────────────────────┬─────────────────────────────┘
                           │ IPC / REST API (Port 5000)
┌──────────────────────────▼─────────────────────────────┐
│                 Python Arka Plan Motoru                │
│    Flask API • Manifest & Steam Store Parser • SQLite   │
└──────────────────────────┬─────────────────────────────┘
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
┌──────────────┐                       ┌──────────────┐
│ Steam Client │                       │  OnlineFix   │
│  (Hook/DLL)  │                       │  (Multiplayer)│
└──────────────┘                       └──────────────┘
```

| Bileşen | Teknoloji | Açıklama |
|---|---|---|
| **Kullanıcı Arayüzü (Frontend)** | Electron 33, HTML5, CSS3, Vanilla JS | Siberpunk mor neon temalı modern, akıcı ve duyarlı arayüz |
| **Arka Plan Çekirdeği (Backend)** | Python 3.14 (Flask API, PyInstaller) | Manifest ayrıştırma, Steam Store API, çoklu indirme motoru |
| **Otomatik Güncelleme** | Electron Updater & GitHub Releases | Hibrit güncelleme motoru (SemVer + Tarih & Hash kontrolü + Manuel onarım) |
| **Veritabanı & Önbellek** | SQLite3 / Yerel JSON Cache | Hızlı arama ve önbellek mekanizması |
| **Paketleyici & Kurulum** | NSIS Installer (x64) | Sessiz, kullanıcı odaklı bağımsız kurulum |

---

## 📋 Sistem Gereksinimleri

| Gereksinim | Detay |
|---|---|
| **İşletim Sistemi** | Windows 10 / Windows 11 (64-bit) |
| **İşlemci / Mimari** | x64 Uyumlu İşlemci |
| **Steam** | Resmi Steam istemcisi kurulu olmalıdır |
| **Yönetici İzni** | Gerekmez (Kullanıcı profiline özel kurulum) |
| **Disk Alanı** | ~150 MB (Uygulama) + Oyun & Yama İndirmeleri |
| **Ağ** | Manifest ve yama indirmeleri için aktif internet bağlantısı |

---

## ❓ Sıkça Sorulan Sorular (SSS)

<details>
<summary><b>1. Oyunu ekledim ancak indirme başlarken "İnternet bağlantısı yok" veya "Lisans yok" diyor?</b></summary>
<br>

Bu durum tamamen Steam istemcisinin eski indirme önbelleğini tutmasından kaynaklanır. Çözümü çok basittir:
1. Steam'in sol üst köşesindeki **Steam** menüsüne tıklayın ve **Ayarlar**'a girin.
2. Sol taraftaki menüden **İndirmeler** sekmesine geçin.
3. Sayfayı aşağı kaydırarak **"İndirme Önbelleğini Temizle"** butonuna basın.
4. Steam yeniden başladığında oyun kütüphanenizde belirecek ve indirme sorunsuz şekilde başlayacaktır.
</details>

<details>
<summary><b>2. OnlineFix yamasıyla arkadaşlarımla nasıl oynarım?</b></summary>
<br>

Arkadaşınızla çok oyunculu oynayabilmek için:
1. İkinizin de aynı oyunu Steam kütüphanesine eklemiş olması gerekir.
2. SteaMRogue arayüzünden ilgili oyun için **OnlineFix yamasını** indirip uygulayın.
3. Oyunu Steam üzerinden başlatın ve Steam arayüzü (**Shift + Tab**) aracılığıyla arkadaşınızı lobiye davet edin.
</details>

<details>
<summary><b>3. Antivirüs veya Windows Defender uyarı verirse ne yapmalıyım?</b></summary>
<br>

Çok oyunculu crack ve kanca dosyaları (SteamTools DLL'leri), oyun fonksiyonlarını yönlendirdikleri için bazı antivirüsler tarafından yanlış pozitif (*false-positive*) olarak algılanabilir. SteaMRogue arayüzündeki **"Defender İstisnası Ekle"** butonunu kullanarak Steam ve uygulama klasörlerini güvenli istisnalara ekleyebilirsiniz.
</details>

<details>
<summary><b>4. Oyuna yeni bir yama veya güncelleme geldiğinde ne yapmalıyım?</b></summary>
<br>

SteaMRogue, kütüphanenizdeki oyunların manifestlerini otomatik olarak senkronize eder. Oyuna resmi güncelleme geldiğinde doğrudan Steam üzerinden indirmeyi başlatabilirsiniz. Herhangi bir takılma durumunda Steam indirme önbelleğini temizlemeniz yeterlidir.
</details>

<details>
<summary><b>5. Otomatik güncelleme nasıl çalışır?</b></summary>
<br>

SteaMRogue başlatıldığında GitHub üzerindeki en son sürümü kontrol eder. Yeni bir sürüm bulunduğunda arka planda indirilir ve ana ekranda **"Güncelleme Hazır"** bildirimi belirir. Butona tıkladığınızda uygulama saniyeler içinde kendini güncelleyip yeniden başlar.
</details>

---

## 🤝 Katkıda Bulunma & Destek

SteaMRogue açık bir projedir. Geri bildirimleriniz, önerileriniz ve katkılarınız projeyi daha ileriye taşımaktadır.

* 🐛 Bir hata mı buldunuz? [GitHub Issues](https://github.com/mythoscd/SteaMRogue/issues) üzerinden bildirin.
* 💡 Yeni bir özellik mi öneriyorsunuz? Bir öneri konusu açın veya Pull Request gönderin.
* ⭐ Projeyi beğendiyseniz sağ üst köşeden bir **Yıldız (Star)** bırakmayı unutmayın!

---

<div align="center">

🎮 **Senin kütüphanen, senin kuralların.**  
Made with ❤️ by [mythoscd](https://github.com/mythoscd)

</div>