<div align="center">

# 🎮 SteaMRogue
### Hepsi Bir Arada Steam Kütüphane Yöneticisi, OnlineFix Multiplayer & Otomatik Güncelleme Platformu

[![Sürüm](https://img.shields.io/badge/S%C3%BCr%C3%BCm-v1.1.5-7c3aed?style=for-the-badge&logo=github)](https://github.com/mythoscd/SteaMRogue/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20(x64)-0078D6?style=for-the-badge&logo=windows)](https://github.com/mythoscd/SteaMRogue/releases/latest)
[![Teknoloji](https://img.shields.io/badge/Mimari-Electron%20%2B%20Python%203.14-success?style=for-the-badge)](https://github.com/mythoscd/SteaMRogue)
[![Otomatik Güncelleme](https://img.shields.io/badge/Otomatik%20G%C3%BCncelleme-Aktif%20(In--App)-orange?style=for-the-badge&logo=electron)](https://github.com/mythoscd/SteaMRogue)
[![Lisans](https://img.shields.io/badge/Lisans-MIT-informational?style=for-the-badge)](LICENSE)

<p align="center">
  <b>SteaMRogue</b>, Steam kütüphanenizi tek tıkla zenginleştiren, oyunları orijinal disk seçim penceresiyle entegre eden, çok oyunculu (OnlineFix) yamalarını otomatik indirip kuran, yerleşik başarımlar (SAM) yöneticisi sunan ve kendi kendini onaran motoruyla daima en son sürümde kalan yeni nesil masaüstü platformudur.
</p>

[🚀 Hızlı Başlangıç](#-hızlı-başlangıç--kurulum) • [✨ Öne Çıkan Özellikler](#-öne-çıkan-özellikler) • [🛠️ Teknoloji Mimarisi](#️-teknoloji-mimarisi) • [❓ Sıkça Sorulan Sorular (SSS)](#-sıkça-sorulan-sorular-sss) • [📦 Sürümler](https://github.com/mythoscd/SteaMRogue/releases)

---

</div>

## 🚀 Hızlı Başlangıç & Kurulum

SteaMRogue, bağımsız tek tık kurulum yürütücüsü (NSIS) ile birlikte gelir. Yönetici (UAC) yetkisi gerektirmez ve doğrudan kullanıcı dizinine kurulur.

### 📥 1. İndirme
En son kararlı sürümü doğrudan aşağıdaki bağlantıdan edinebilirsiniz:
* ⬇️ **[SteaMRogue-Setup-1.1.5.exe (Doğrudan İndir)](https://github.com/mythoscd/SteaMRogue/releases/download/v1.1.5/SteaMRogue-Setup-1.1.5.exe)**
* 📋 Tüm geçmiş ve güncel sürümler için: **[GitHub Releases](https://github.com/mythoscd/SteaMRogue/releases)**

### ⚡ 2. Kurulum
1. İndirdiğiniz `SteaMRogue-Setup-1.1.5.exe` dosyasını çalıştırın.
2. Kurulum otomatik olarak tamamlanır ve masaüstünüze **SteaMRogue** kısayolu eklenir.
3. Uygulama açıldığında Steam istemcinizi otomatik olarak algılar, arka plan bileşenlerini eşitler ve kullanıma hazır hale gelir.

> [!TIP]
> **Yerleşik Otomatik Güncelleme (In-App Auto-Update):**  
> Kurulumu bir kez yaptıktan sonra manuel olarak yeni sürüm aramanıza gerek yoktur. SteaMRogue her açılışta güncellemeleri arka planda denetler ve yeni bir sürüm çıktığında tek tıkla kendisini günceller.

---

## ✨ Öne Çıkan Özellikler

### 🎮 1. Akıllı Kütüphane Izgarası & 20'li Sayfalama
* **10 Üst + 10 Alt Izgara Düzeni:** Geniş ekranlarda 1. satırda 10, 2. satırda 10 olmak üzere sayfa başına tam 20 oyunluk poster yerleşimi sağlar.
* **Dinamik Sayfalama:** 20 oyunu aşan kütüphanelerde `Sayfa 1/2`, `Sonraki >` ve `< Önceki` kontrolleri devreye girer. Arama veya filtreleme yapıldığında otomatik olarak ilk sayfaya döner.
* **Sıfır Boşluklu Tasarım:** Kütüphane kutusu dikeyde esneyerek sayfanın altındaki boş siyah alanları tamamen kapatır ve gereksiz kaydırma çubuklarını engeller.
* **Çok Yönlü Arama & Ekleme:** Sayısal **AppID**, doğrudan **Oyun Adı** veya tarayıcınızdan kopyaladığınız **Steam Mağaza Linkleri** (`store.steampowered.com/app/...`) ile anında oyun ekleyin.
* **Serbest Disk Seçimi:** Sahte ACF yapılandırmalarıyla sisteminizi C: sürücüsüne zorlamaz; oyunu kurarken Steam'in kendi resmi penceresinden istediğiniz diski (C, D veya harici SSD) seçebilirsiniz.
* **Tek Tıkla Steam Yeniden Başlatıcı:** Kütüphane değişikliklerinin anında geçerli olması için Steam istemcisini arka plan kilitlenmelerine yol açmadan tek tıkla güvenle yeniden başlatır.

### 🏆 2. Entegre Başarımlar (SAM — Steam Achievement Manager)
* **Tam Uyumlu Yerel Arayüz:** Üçüncü taraf bağımsız pencereler yerine SteaMRogue'un siberpunk mor/neon temasıyla birebir uyumlu yerel başarımlar modülü.
* **Gelişmiş Başarım Yönetimi:** Kütüphanenizdeki oyunların başarımlarını listeleyin, istatistikleri görüntüleyin, tek tek veya topluca kilitleyip açın.

### 🚀 3. Canlı Senkronizasyon & Modern Açılış Ekranı (Splash Screen)
* **Canlı Açılış Ekranı:** Uygulama başlatılırken animasyonlu yüklenme çubuğu eşliğinde sistem bileşenleri, SteamTools DLL kancaları, TOML imzaları ve manifest depoları arka planda eşitlenir.
* **Dinamik Arka Plan Takibi:** Eşitleme bittiği anda durum kendiliğinden yeşil **`GÜNCEL`** rozetine dönüşür.
* **Yanıltıcı Bildirimler Giderildi:** Dosyalar yerindeyken oluşan yanıltıcı *"Yeniden Başlatma Gerekli"* ve asılı kalan *"Kontrol ediliyor..."* durumları giderilmiş, rahatlatıcı yeşil durumlar getirilmiştir.

### 🧩 4. Sistem Bağımlılıkları (Microsoft Visual C++ 2015-2022)
* **Çift Mimari Denetimi:** Steam 32-bit (`SysWOW64\vcruntime140.dll`) ve oyunlar/OnlineFix 64-bit (`System32\vcruntime140.dll`) kütüphaneleri eksiksiz taranır.
* **Tek Tıkla Sessiz Kurulum:** Eksik olması durumunda resmi Microsoft CDN sunucularından indirilerek arka planda sessizce kurulur.

### 🛡️ 5. Antivirüs Yanlış Pozitif Koruması & Karantinadan Kurtarma
* **Otomatik Güvenlik Algılama:** Sistemdeki aktif antivirüs (Windows Defender, Avast, Kaspersky vb.) otomatik tespit edilir.
* **Karantinadan Otomatik Kurtarma:** Güvenlik yazılımı kilit açıcı dosyaları yanlışlıkla silerse veya engellerse, SteaMRogue bunları tek tıkla dahili temiz yedeğinden geri yükler.
* **Tüm Diskler İçin Dışlama:** Farklı disklerdeki tüm Steam kütüphaneleri tek tıkla Windows Defender dışlamalarına eklenir; harici antivirüsler için istisna yolları tek tıkla kopyalanır.

### 🌐 6. OnlineFix Çok Oyunculu (Multiplayer) Desteği
* **Doğrudan Veritabanı Taraması:** Kütüphanenizdeki veya aradığınız herhangi bir oyun için OnlineFix altyapısında anında çok oyunculu yama taraması yapar.
* **Yüksek Hızlı İndiriciler:** Pixeldrain, Gofile ve alternatif sunucularla kesintisiz indirme.
* **Otomatik Kurulum & Entegrasyon:** İndirilen çok oyunculu yamaları otomatik arşivden çıkarır ve oyun dizinine uygular.

### 🏷️ 7. SteamDB İndirim Fırsatları Radarı
* Steam üzerindeki aktif indirimleri anlık olarak tarar.
* Tür, indirim oranı (%70+, %80+, %90+) ve maksimum fiyat filtreleriyle en avantajlı fırsatları listeler.

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
| **Başarımlar (SAM Engine)** | .NET / C# SAMWorker & SteamWorks API | Yerel başarımları listeleme, kilitleme ve açma motoru |
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
| **Disk Alanı** | ~180 MB (Uygulama) + Oyun & Yama İndirmeleri |
| **Ağ** | Manifest ve yama indirmeleri için aktif internet bağlantısı |

---

## ❓ Sıkça Sorulan Sorular (SSS)

<details>
<summary><b>1. Oyunu ekledim ancak indirme başlarken "İnternet bağlantısı yok" veya "Lisans yok" diyor?</b></summary>
<br>

Bu durum tamamen Steam istemcisinin eski indirme önbelleğini tutmasından kaynaklanır. Çözümü çok basittir:
1. SteaMRogue **Ayarlar** sekmesine gidin.
2. SteamTools kartındaki **"İndirme Önbelleğini Temizle"** butonuna basın.
3. Steam otomatik olarak önbelleğini temizleyip yeniden başladığında indirme sorunsuz şekilde başlayacaktır.
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

Çok oyunculu crack ve kanca dosyaları (SteamTools DLL'leri), oyun fonksiyonlarını yönlendirdikleri için bazı antivirüsler tarafından yanlış pozitif (*false-positive*) olarak algılanabilir. SteaMRogue arayüzündeki **"Defender Dışlaması Ekle"** butonunu kullanarak Steam ve uygulama klasörlerini güvenli istisnalara ekleyebilirsiniz. Dosyalar karantinaya alınmışsa **"Karantinadan Kurtar ve Onar"** düğmesiyle anında kurtarabilirsiniz.
</details>

<details>
<summary><b>4. Başarımları nasıl açıp kapatabilirim?</b></summary>
<br>

1. Üst menüden **Başarımlar** sekmesine tıklayın.
2. Kütüphanenizdeki oyunu seçin.
3. Açmak istediğiniz başarımların kutucuklarını işaretleyin ve sağ üstteki **"Değişiklikleri Kaydet"** butonuna basın.
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