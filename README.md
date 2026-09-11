<div align="center">

# 🎮 SteaMRogue
### Yeni Nesil Steam Kütüphane, Kilit Açma ve Multiplayer Yama Yöneticisi

[![Release](https://img.shields.io/github/v/release/mythoscd/SteaMRogue?style=for-the-badge&color=7c3aed&label=S%C3%BCr%C3%BCm)](https://github.com/mythoscd/SteaMRogue/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-blue?style=for-the-badge&logo=windows)](https://github.com/mythoscd/SteaMRogue/releases)
[![License](https://img.shields.io/badge/Durum-Aktif%20%26%20G%C3%BCncel-brightgreen?style=for-the-badge)](https://github.com/mythoscd/SteaMRogue)
[![Auto Update](https://img.shields.io/badge/Otomatik%20G%C3%BCncelleme-Aktif-orange?style=for-the-badge&logo=github)](https://github.com/mythoscd/SteaMRogue)

<p align="center">
  <b>SteaMRogue</b>, oyuncuların Steam kütüphanelerini diledikleri gibi yönetmelerini sağlayan, SteamTools altyapısıyla güçlendirilmiş, otomatik OnlineFix çok oyunculu yama desteği ve yerleşik otomatik güncelleme motoruna sahip modern bir masaüstü uygulamasıdır.
</p>

[📥 En Son Sürümü İndir (v1.0.6)](https://github.com/mythoscd/SteaMRogue/releases/latest) • [✨ Özellikler](#-öne-çıkan-özellikler) • [🚀 Kurulum](#-kurulum) • [📖 Kullanım](#-kullanım-rehberi) • [❓ SSS](#-sıkça-sorulan-sorular-sss)

---

</div>

## 🌟 Öne Çıkan Özellikler

### 1. 🎯 Orijinal Steam Kütüphanesi & Disk Seçimi
* Eklenen tüm oyunlar doğrudan Steam istemcinizin kütüphanesine orijinal lisanslı gibi eklenir.
* Sahte veya diski kısıtlayan manifestler yerine **Steam'in orijinal kurulum ekranını** kullanır.
* Oyunu yüklerken Steam arayüzünden istediğiniz diski (**C:**, **D:** veya harici SSD) kendiniz özgürce seçebilirsiniz.
* Disk yetersizliği veya zorunlu C: ataması hataları tamamen tarihe karışır.

### 2. 🌐 OnlineFix & Çok Oyunculu (Multiplayer) Yama Motoru
* Kütüphanenizdeki veya aradığınız herhangi bir oyun için OnlineFix veritabanında anında yama taraması yapar.
* **Gelişmiş Çoklu Hoster Desteği:**
  * ⚡ **Pixeldrain API** (Yüksek hızlı doğrudan indirme)
  * 🚀 **Gofile Entegrasyonu** (Token ve salt çözücü ile kesintisiz indirme)
  * 🛡️ **FileDitch & Alternatif Aynalar**
* İndirilen yamayı otomatik olarak şifresini çözerek açar ve oyunun kurulu olduğu dizine **tek tıkla entegre eder**. Artık dosyaları elle taşımakla uğraşmanıza gerek yok!

### 3. 🚀 Yerleşik Otomatik Güncelleme (Auto-Update Engine)
* Uygulama, açılışta ve çalışma esnasında yeni sürümleri GitHub Releases üzerinden sessizce denetler.
* Yeni bir güncelleme yayınlandığında ekranın sağ alt köşesinde şık bir bildirim kartı belirir ve güncellemeyi arka planda otomatik olarak indirir.
* Kullanıcı tek bir butona tıklayarak tarayıcı veya link aramadan saniyeler içinde en son sürüme yükseltir.

### 4. 🛡️ Akıllı Güvenlik & İstisna Asistanı
* Windows Defender ve üçüncü taraf antivirüslerin oluşturduğu yanlış pozitif (false-positive) dosya silme sorunlarına son verir.
* Steam klasörünüzü tek tıkla Windows Güvenliği İstisnalarına ekleyen yerleşik istisna yardımcısı içerir.

### 5. 🎨 Modern Project Lightning Arayüzü
* Göz yormayan, modern, karanlık (dark mode) neon mor/mavi estetiğe sahip tasarım.
* Kütüphane oyun kapakları, arama filtreleri ve anlık indirme ilerleme çubukları ile donatılmış akıcı kullanıcı deneyimi.

---

## 📥 Kurulum

1. **[Releases](https://github.com/mythoscd/SteaMRogue/releases/latest)** sayfasına gidin.
2. `SteaMRogue Setup X.X.X.exe` dosyasını indirin.
3. İndirdiğiniz kurulum dosyasına çift tıklayın. Kurulum tamamen sessiz ve otomatiktir; birkaç saniye içinde Masaüstünüze **SteaMRogue** kısayolu eklenecektir.
4. Uygulamayı çalıştırın ve kütüphanenizi yönetmeye başlayın!

> [!NOTE]
> SteaMRogue kendi içinde otomatik güncelleme motoruna sahip olduğu için bu kurulumu yalnızca **ilk defa** yapmanız yeterlidir. Gelecekte çıkacak tüm yeni sürümler uygulama içerisinden otomatik olarak güncellenecektir.

---

## 📖 Kullanım Rehberi

### 🎮 Yeni Bir Oyun Eklemek
1. SteaMRogue'u açın ve üst kısımdaki arama çubuğuna eklemek istediğiniz oyunun adını veya Steam AppID'sini yazın.
2. Çıkan sonuçtan oyunu seçip **"Kütüphaneye Ekle"** butonuna tıklayın.
3. İşlem tamamlandığında Steam istemcinizi yeniden başlatın.
4. Steam Kütüphanenizden oyunu bulun ve mavi **"YÜKLE"** butonuna tıklayın.
5. Açılan orijinal Steam penceresinden oyunu kurmak istediğiniz diski (C:, D: vb.) seçip indirmeyi başlatın!

### 🌐 Multiplayer (OnlineFix) Yaması Uygulamak
1. SteaMRogue içerisinden **"OnlineFix Yamaları"** bölümüne gelin.
2. Oynamak istediğiniz oyunu aratın.
3. **"Yamayı İndir"** dedikten sonra açılan pencereden **"Oyuna Entegre Et"** seçeneğini seçin.
4. Sistem yamayı indirecek, arşivden çıkaracak ve oyun klasörünüze otomatik yerleştirecektir.
5. Oyunu açıp arkadaşlarınızla birlikte multiplayer oynamaya başlayabilirsiniz!

---

## ❓ Sıkça Sorulan Sorular (SSS)

<details>
<summary><b>1. Oyun yüklerken diski kendim seçebilir miyim?</b></summary>
<br>
<b>Evet!</b> SteaMRogue, oyunları diske önceden sabitlemez. Steam'in orijinal yükleme penceresini tetikler; böylece Windows 11 (C:) veya Yeni Birim (D:) gibi istediğiniz diski Steam arayüzünden doğrudan kendiniz seçebilirsiniz.
</details>

<details>
<summary><b>2. Yeni bir güncelleme geldiğinde ne yapmam gerekiyor?</b></summary>
<br>
Hiçbir şey yapmanıza gerek yoktur. Uygulamayı açtığınızda sağ altta <i>"Yeni Güncelleme Mevcut!"</i> bildirimi çıkacak ve güncelleme otomatik inecektir. İndirme bittiğinde <i>"Şimdi Güncelle & Yeniden Başlat"</i> butonuna basmanız yeterlidir.
</details>

<details>
<summary><b>3. Antivirüs veya Windows Defender uyarı verirse ne yapmalıyım?</b></summary>
<br>
Oyun kilit açma araçları (SteamTools / SmokeAPI ve OnlineFix DLL dosyaları) oyun kodlarına müdahale ettiği için antivirüsler bazen "Yanlış Pozitif (False Positive)" alarmı verebilir. SteaMRogue Ayarlar menüsünden <b>"İstisna Ekle"</b> butonunu kullanarak Steam klasörünüzü güvenli listeye ekleyebilirsiniz.
</details>

<details>
<summary><b>4. OnlineFix yamalarında şifre girmem gerekiyor mu?</b></summary>
<br>
Hayır. SteaMRogue, OnlineFix arşiv şifrelerini (<code>online-fix.me</code> vb.) yerleşik algoritmasıyla otomatik olarak girer ve dosyaları kendisi açar.
</details>

---

## 💻 Sistem Gereksinimleri

| Bileşen | Minimum Gereksinim | Önerilen |
| :--- | :--- | :--- |
| **İşletim Sistemi** | Windows 10 (64-bit) | Windows 11 (64-bit) |
| **İşlemci** | Çift çekirdekli 1.8 GHz | Dört çekirdekli 2.5 GHz veya üzeri |
| **Bellek (RAM)** | 2 GB RAM | 4 GB RAM veya üzeri |
| **Depolama** | 250 MB boş alan | SSD Depolama |
| **Steam** | Güncel Steam İstemcisi | Güncel Steam İstemcisi |

---

<div align="center">

Geliştirici: **[@mythoscd](https://github.com/mythoscd)**  
*SteaMRogue Projesi — Tüm Hakları Saklıdır.*

</div>
