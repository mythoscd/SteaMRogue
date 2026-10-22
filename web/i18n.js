/* ==========================================================================
   SteaMRogue Internationalization (i18n) Engine
   Complete Dual-Language Dictionary (Turkish 🇹🇷 & English 🇬🇧)
   Zero Untranslated Text - 100% Comprehensive Coverage
   ========================================================================== */

(function () {
    const translations = {
        tr: {
            // --- HEADER & NAV ---
            "app_title": "SteaMRogue",
            "nav_library": "Kütüphane",
            "nav_onlinefix": "OnlineFix",
            "nav_bypass": "Bypass",
            "nav_deals": "İndirimler",
            "nav_achievements": "Başarımlar",
            "nav_import": "İçe Aktar",
            "nav_settings": "Ayarlar",
            "btn_minimize": "Simge Durumuna Küçült",
            "btn_maximize": "Büyüt / Geri Yükle",
            "btn_close": "Kapat",
            "select_language": "Dil Seçimi / Select Language",

            // --- SUB-HEADER / ACTIONS & CLOCK ---
            "system_time": "SİSTEM SAATİ",
            "loading_clock": "Yükleniyor...",
            "btn_how_to": "Nasıl Yapılır?",
            "search_placeholder": "Steam mağaza linki, AppID veya oyun adı girin (Örn: store.steampowered.com/app/...)...",
            "btn_add_to_library": "Kütüphaneye Ekle",
            "btn_restart_steam": "Steam'i Yeniden Başlat",
            "btn_restart_steam_title": "Steam istemcisini güvenle yeniden başlatır",
            "mode_safe": "Güvenli Mod",
            "mode_safe_title": "Kilit açıcı kancaları kaldırır. CS2 ve VAC korumalı oyunlar için %100 temiz ve güvenlidir.",
            "mode_steamrogue": "SteaMRogue Modu",
            "mode_steamrogue_title": "SteaMRogue kütüphane kilitlerini açar ve oyunları aktifleştirir.",
            "mode_help_tooltip": "Çalışma Modları ve VAC Güvenliği Hakkında Bilgi",
            "mode_restart_needed": "Yeniden Başlatma Gerekli",

            // --- LIBRARY TAB ---
            "lib_title": "Oyun Kütüphaneniz",
            "lib_games_count": "{count} oyun",
            "lib_sort_newest": "En Yeni",
            "lib_sort_az": "A-Z",
            "lib_refresh": "Yenile",
            "lib_refresh_title": "Kütüphaneyi Yenile",
            "lib_search_placeholder": "Kütüphanede ara...",
            "lib_prev": "Önceki",
            "lib_next": "Sonraki",
            "lib_page_info": "Sayfa {current}/{total}",
            "lib_empty_title": "Henüz kütüphanenize oyun eklenmedi.",
            "lib_empty_desc": "Yukarıdaki arama çubuğundan bir oyun linki, AppID veya isim yazıp ekleyebilirsiniz.",
            "badge_installed": "YÜKLÜ",
            "badge_downloadable": "İNDİRİLEBİLİR",
            "ctx_launch_game": "Oyunu Başlat",
            "ctx_browse_files": "Dosya Konumunu Aç",
            "ctx_open_in_steam": "Steam'de Görüntüle",
            "ctx_manage_achievements": "Başarımları Yönet",
            "ctx_check_onlinefix": "OnlineFix Yamasını İncele",
            "ctx_remove_game": "Kütüphaneden Kaldır",

            // --- DEALS TAB ---
            "deals_title": "İndirim Fırsatları",
            "deals_badge": "Steam Özel İndirimleri",
            "deals_refresh": "Yenile",
            "deals_search_placeholder": "İndirimlerde oyun ara (örn. Witcher, Cyberpunk)...",
            "deals_clear_search": "Aramayı Temizle",
            "deals_notice_note": "Not:",
            "deals_notice_text": "Oyun kategorileri Steam verilerine göre filtrelenmektedir; bazı kategorilerde küçük hatalar olabilir.",
            "deals_genre_label": "Tür:",
            "deals_genre_all": "Tümü",
            "deals_genre_action": "Aksiyon",
            "deals_genre_adventure": "Macera",
            "deals_genre_rpg": "RPG",
            "deals_genre_strategy": "Strateji",
            "deals_genre_simulation": "Simülasyon",
            "deals_genre_sports": "Spor",
            "deals_genre_indie": "Bağımsız (Indie)",
            "deals_discount_label": "İndirim:",
            "deals_max_price_label": "Maks. Fiyat:",
            "deals_loading": "Aktif Steam indirimleri yükleniyor...",

            // --- ACHIEVEMENTS TAB (SAM) ---
            "ach_title": "Başarımlar (SAM)",
            "ach_subtitle_tag": "Steam Achievement Manager",
            "ach_desc": "Steam hesabınızdaki oyunların başarımlarını görüntüleyin ve yönetin.",
            "ach_library_games_label": "Kütüphanenizdeki Oyunlar:",
            "ach_btn_refresh": "Yenile",
            "ach_btn_refresh_title": "Kütüphaneyi Yeniden Tara",
            "ach_search_placeholder": "Kütüphanenizdeki oyunlar arasında arama yapın veya AppID yazın (Örn: Counter-Strike, Cyberpunk, 730)...",
            "ach_scanning_title": "Kütüphaneniz taranıyor...",
            "ach_scanning_desc": "Steam oyunlarınız ve başarımlar listeleniyor",
            "ach_modal_title": "Oyun Başarımları",
            "ach_modal_unlocked": "Açılan:",
            "ach_modal_rate": "Tamamlanma Oranı:",
            "ach_btn_unlock_all": "Tümünü Aç",
            "ach_btn_lock_all": "Tümünü Kilitle",
            "ach_btn_invert": "Tersine Çevir",
            "ach_modal_search_placeholder": "Başarım ara...",
            "ach_btn_save_steam": "Steam'e Kaydet",
            "ach_modal_status_hint": "Değişiklikleri kaydetmek için Steam'e Kaydet butonuna basın.",

            // --- IMPORT TAB ---
            "imp_title": "Dosya İçe Aktar",
            "imp_desc": "İndirdiğiniz Steam manifest (.manifest), kilit açma konfigürasyonu (.lua) veya arşiv dosyalarını (.zip) sürükleyip bırakarak kolayca Steam'e aktarın.",
            "imp_drop_title": "Dosyaları Buraya Sürükleyin ve Bırakın",
            "imp_drop_sub": "Desteklenen formatlar: .lua, .zip, .manifest",
            "imp_btn_browse": "Dosya Seç",
            "imp_how_to_use": "Nasıl Kullanılır:",
            "imp_rule_manifest": ".manifest dosyaları: İlgili depot manifest dosyasını doğru dizine yerleştirir.",
            "imp_rule_lua": ".lua dosyaları: Kilit açma betiklerini Steam yapılandırma klasörüne kopyalar.",
            "imp_rule_zip": ".zip paketleri: Arşiv içeriğini otomatik olarak ilgili Steam dizinlerine çıkartır.",

            // --- SETTINGS TAB ---
            "set_main_title": "Uygulama Ayarları & Sistem Yönetimi",
            "set_main_desc": "Steam kilit açıcılarını, otomatik güncellemeleri, kütüphane onarımlarını ve güvenlik entegrasyonlarını yönetin.",
            "set_app_update_title": "SteaMRogue Uygulama Güncellemesi",
            "set_app_update_desc": "Uygulama GitHub Releases üzerinden otomatik güncellenir. Dilediğiniz zaman yeni sürüm kontrolü yapabilir veya mevcut kurulumu onarabilirsiniz.",
            "set_app_update_status": "Otomatik güncelleme motoru aktif.",
            "set_btn_check_update": "Güncellemeleri Denetle",
            "set_btn_repair_install": "Son Sürümü Yeniden İndir / Onar",
            "set_sync_title": "Bileşen, Manifest & İmza Senkronizasyonu (Canlı Motor)",
            "set_sync_badge": "GÜNCEL",
            "set_sync_desc": "SteamTools kilit açıcıları, OpenSteamTool TOML imzaları, topluluk manifest veritabanları, OnlineFix bypass listesi ve kütüphanenizdeki oyunların Lua betikleri her açılışta arka planda tam hızla eşitlenir.",
            "set_sync_status": "Tüm depolar, kancalar ve manifest kaynakları aktif.",
            "set_btn_sync_now": "Bileşenleri & İmzaları Şimdi Güncelle",
            "set_st_dll_label": "SteamTools DLL:",
            "set_st_dll_status": "Eşitlendi",
            "set_toml_sig_label": "TOML İmzaları:",
            "set_toml_sig_status": "Dinamik Uyumlu",
            "set_manifest_repo_label": "Manifest Depoları:",
            "set_manifest_repo_status": "4/4 Aktif",
            "set_of_bypass_label": "OnlineFix Bypass:",
            "set_of_bypass_status": "Çevrimiçi Eşit",

            "set_steam_dir_title": "Steam Kurulum Dizini",
            "set_steam_dir_helper": "Boş bırakılırsa Windows kayıt defterinden (Registry) otomatik tespit edilir.",
            "set_btn_save_dir": "Dizini Kaydet",

            "set_self_heal_title": "Kendi Kendini Onaran Sistem (Self-Healing)",
            "set_self_heal_badge": "SAĞLIKLI",
            "set_self_heal_desc": "SteaMRogue her açılışta Steam kilit açıcılarını, LUA yapılandırmalarını, Spacewar (480) çevrimiçi kaydını, 7-Zip araçlarını ve bozuk önbellekleri otomatik tarayıp onarır.",
            "set_self_heal_status": "Tüm bileşenler, kancalar ve servisler aktif ve doğrulanmış durumda.",
            "set_btn_self_heal": "Sistemi Otomatik Tara ve Onar",

            "set_st_hook_title": "SteamTools Kancası (OpenSteamTool)",
            "set_st_hook_desc": "Gerekli kilit açıcı DLL dosyalarını (dwmapi.dll, xinput1_4.dll, OpenSteamTool.dll) Steam ana klasörüne yerleştirir.",
            "set_hook_status_label": "Kanca Durumu:",
            "set_hook_status_active": "AKTİF (HER ŞEY YOLUNDA)",
            "set_detected_files_label": "Tespit Edilen Dosyalar:",
            "set_none": "Yok",
            "set_btn_install_st": "SteamTools Kur / Onar",
            "set_btn_restart_steam_st": "Steam'i Yeniden Başlat",
            "set_btn_clear_cache_st": "İndirme Önbelleğini Temizle (\"İnternet Yok\" Çözümü)",
            "set_btn_uninstall_st": "SteamTools Kaldır",

            "set_vcredist_title": "Sistem Bağımlılıkları (Microsoft Visual C++ 2015-2022)",
            "set_vcredist_badge": "KURULU (HER ŞEY YOLUNDA)",
            "set_vcredist_desc": "Oyunların çökmeden açılması, SteamTools kilit açıcılarının ve OnlineFix çok oyunculu modüllerinin çalışması için 32-bit (x86) ve 64-bit (x64) Visual C++ kütüphaneleri zorunludur.",
            "set_vcredist_status": "Microsoft Visual C++ (x86 & x64) sisteminizde eksiksiz kurulu, her şey yolunda.",
            "set_btn_install_vcredist": "Eksik Paketleri Otomatik İndir & Kur",

            "set_av_title": "Antivirüs & Güvenlik Ayarları (Karantina Önleme)",
            "set_av_badge": "GÜVENLİ (SORUN YOK)",
            "set_av_desc": "SteaMRogue ve SteamTools dosyalarının Windows Defender veya harici antivirüsler tarafından yanlışlıkla silinmesini veya karantinaya alınmasını önleyin.",
            "set_av_status": "Kilit açıcı kütüphaneler karantinaya alınmamış, yerinde duruyor. Her şey yolunda.",
            "set_btn_restore_quarantine": "Karantinadan Kurtar ve Onar",
            "set_btn_add_defender_exclusion": "Windows Defender Dışlaması Ekle",
            "set_external_av_title": "Harici Antivirüs (Avast/Kaspersky vb.) Kullananlar İçin:",
            "set_external_av_desc": "İstisnalar (Exceptions / Exclusions) listesine Steam ve SteaMRogue klasörlerini eklemeniz yeterlidir.",
            "set_btn_copy_exclusion_paths": "İstisna Yollarını Kopyala",

            "set_disclaimer_title": "Yasal Uyarı & Kullanıcı Sorumluluk Beyanı",
            "set_disclaimer_desc": "İlk açılışta sunulan yasal sorumluluk bildirimini, VAC koruma hatırlatmasını ve kullanım koşullarını dilediğiniz zaman tekrar inceleyebilirsiniz.",
            "set_btn_view_disclaimer": "Bildirimi Görüntüle",

            "set_danger_title": "Tehlike Bölgesi: Sistemi İmha Et & Kaldır",
            "set_danger_desc": "SteamTools kancasını kaldırır, kütüphanedeki oyun manifestolarını ve LUA yapılandırmalarını siler, Bypass ile oyunlara uygulanan fix dosyalarını temizler ve SteaMRogue'u sistemden tamamen siler.",
            "set_btn_nuke": "Sistemi Tamamen İmha Et & Kaldır",

            // --- ONLINEFIX TAB ---
            "of_title": "OnlineFix Çok Oyunculu Yamalar",
            "of_rar_pw_label": "İndirilen arşivlerin şifresi:",
            "of_search_placeholder": "Yama ara (Örn: Palworld, Ready or Not)...",
            "of_btn_search": "Ara",
            "of_info_title": "Önemli Bilgilendirme ve Notlar",
            "of_note1_title": "Antivirüs & Koruma Ayarları",
            "of_note1_text": "Yamaların sorunsuz entegre edilebilmesi ve oyunun açılması için Windows Güvenliği > Gerçek zamanlı korumayı ve varsa harici antivirüsünüzü geçici olarak kapatmalısınız. Aksi halde Windows, yama dosyalarını silebilir. (Korumayı sadece oyunu açarken ve oynarken kapalı tutmanız yeterlidir; oyundan çıktıktan sonra tekrar açabilirsiniz.)",
            "of_note2_title": "Multiplayer / Eşleşme Notu",
            "of_note2_text": "Online-Fix yamalı oyunlar sadece aynı yamayı kullanan diğer oyuncularla online oynanabilir. Oyunu orijinal alan kişilerle eşleşemezsiniz. Birlikte oynayacağınız arkadaşlarınızın da yamayı kurması gerekir.",
            "of_dl_heading": "Multiplayer Yama İndiriliyor",
            "of_dl_file_loading": "Dosya: Bağlantılar çözümleniyor...",
            "of_dl_starting": "İndirme başlatılıyor...",
            "of_btn_open_download": "İndirilen Dosyayı Aç",
            "of_btn_cancel_download": "İptal Et",
            "of_search_prompt": "OnlineFix üzerinden çok oyunculu (multiplayer) yama aramak için yukarıdaki arama kutusunu kullanın.",
            "of_library_games_title": "Kütüphane Oyunları",

            // --- BYPASS TAB ---
            "bp_search_placeholder": "Bu kategoride oyun ara...",
            "bp_loading_games": "Oyun listesi ve kapakları yükleniyor...",
            "bp_btn_back": "Oyun Listesine Dön",
            "bp_label_notes": "Kurulum & Kullanım Notları",
            "bp_label_known_issues": "Bilinen Sorunlar ve Çözümleri",
            "bp_label_software": "Gerekli Ek Yazılımlar",
            "bp_label_config": "Oyun Yapılandırması",
            "bp_key_appid": "App ID",
            "bp_key_direct_exe": "Doğrudan EXE ile Başlat",
            "bp_key_steam_launch": "Steam Üzerinden Başlat",
            "bp_key_fix_type": "Fix Türü",
            "bp_btn_apply_fix": "Fix Uygula",

            // --- BYPASS CHOICE MODAL ---
            "bp_modal_choice_title": "Bypass Fix Yükleme Seçeneği",
            "bp_modal_choice_desc": "Lütfen fix dosyalarının nasıl uygulanmasını istediğinizi seçin:",
            "bp_opt_auto_title": "Otomatik Tespit Et & Kur",
            "bp_opt_auto_badge": "Önerilen",
            "bp_opt_auto_desc": "Tüm disklerdeki (C:, D:, E: vb.) Steam kütüphanelerini tarar, oyun klasörünü otomatik bularak fix dosyalarını güvenle kurar.",
            "bp_opt_manual_title": "Manuel Klasör Seç",
            "bp_opt_manual_desc": "Steam kütüphanesini (steamapps\\common) otomatik açar, oyun klasörünü kendiniz seçersiniz.",
            "bp_choice_warning": "Otomatik tespit oyununuzu bulamazsa veya oyun henüz kurulu değilse hiçbir işlem yapılmaz ve güvenliğiniz için manuel seçim penceresi açılır.",
            "bp_btn_cancel": "İptal",

            // --- DEFENDER WARNING MODAL ---
            "def_modal_title": "Windows Defender Uyarısı",
            "def_modal_body": "Fix uygulamadan önce oyun klasörünü Windows Defender dışlama listesine eklemelisin. Aksi halde işlem doğru çalışmayabilir.",
            "def_modal_question": "Oyun klasörünü istisnaya ekledin mi?",
            "def_btn_no": "Hayır",
            "def_btn_yes": "Evet, Devam Et",

            // --- ONLINEFIX CHOICE MODAL ---
            "of_modal_choice_title": "OnlineFix Yama Yükleme Seçeneği",
            "of_modal_choice_desc": "Lütfen multiplayer yamasının nereye yüklenmesini istediğinizi seçin:",
            "of_opt_desktop_title": "Masaüstüne İndir",
            "of_opt_desktop_desc": "Yama arşiv dosyasını sadece Masaüstünüze indirir. Kurulumu elle yapmanız gerekir.",
            "of_opt_integrate_title": "Oyuna Entegre Et",
            "of_opt_integrate_badge": "Önerilen",
            "of_opt_integrate_desc": "Yamayı indirir, şifresini (online-fix.me) girerek otomatik açar, oyunun klasörüne entegre eder ve indirme çöplerini siler.",
            "of_choice_warning_title": "Önemli Not:",
            "of_choice_warning_text": "\"Oyuna Entegre Et\" seçeneğinin çalışması için oyunun kütüphanenizde ve bilgisayarınızda yüklü olması gerekir. Aksi takdirde işlem başarısız olur veya oyun dosyaları bozulabilir!",
            "of_btn_cancel": "İptal",

            // --- HOW TO USE GUIDE MODAL ---
            "guide_modal_title": "Nasıl Oyun Eklenir?",
            "guide_step1_title": "Oyun Linki, AppID veya İsim Girin",
            "guide_step1_desc": "Kutucuğa eklemek istediğiniz oyunun Steam mağaza linkini, AppID numarasını veya adını yazın (Örn: https://store.steampowered.com/app/477160 veya 477160).",
            "guide_step2_title": "Kütüphaneye Ekle'ye Tıklayın",
            "guide_step2_desc": "\"Kütüphaneye Ekle\" butonuna basın. SteaMRogue oyun lisansını kütüphanenize otomatik tanımlar.",
            "guide_step3_title": "Steam'i Yeniden Başlatın",
            "guide_step3_desc": "\"Steam'i Yeniden Başlat\" butonuna tıklayın. Steam tekrar açıldığında oyun kütüphanenizde belirecek ve indirmeye hazır olacaktır!",
            "guide_btn_confirm": "Anladım",

            // --- MODE INFO GUIDE MODAL ---
            "mode_modal_title": "SteaMRogue Çalışma Modları Rehberi",
            "mode_safe_heading": "🛡️ Güvenli Mod (Safe Mode)",
            "mode_safe_desc": "Arka plandaki SteamTools ve oyun ekleme servisleri tamamen sonlandırılır. Daha önce kütüphanenize eklediğiniz oyunlar asla kilitlenmez, kaybolmaz veya 'Satın Alın' uyarısı vermez; kütüphanenizde oynanabilir kalır. Yalnızca yeni oyun ekleme araçları dinlenmeye alınır.",
            "mode_safe_foot": "🛡️ Oyunlarınız daima kütüphanenizde korunur ve SteamTools arka planda çalışmaz.",
            "mode_rogue_heading": "⚡ SteaMRogue Modu",
            "mode_rogue_desc": "SteamTools ve kütüphane ekleme motoru arka planda aktiftir. SteaMRogue üzerinden tek tıkla aradığınız tüm oyunları ve DLC'leri kütüphanenize ekleyebilir, doğrudan Steam üzerinden indirip oynayabilirsiniz.",
            "mode_rogue_foot": "⚡ Oyun eklemek ve kütüphanenizi genişletmek için bu modu kullanın.",
            "mode_switch_heading": "🔄 Anında Geçiş & Sıfır Bekleme",
            "mode_switch_desc": "İster arayüzdeki anahtardan, ister Windows görev çubuğu / sistem tepsisindeki sağ tık menüsünden tek tıkla modlar arasında anında geçiş yapabilirsiniz.",
            "mode_btn_confirm": "Anladım",

            // --- DISCLAIMER & EULA MODAL (10s) ---
            "disc_header_title": "Yasal Uyarı ve Kullanıcı Sorumluluk Beyanı",
            "disc_lead": "SteaMRogue, yerel kütüphane organizasyonu ve bağımsız araç yönetimi sağlayan açık kaynaklı bir yardımcı yazılımdır.",
            "disc_main_text": "Bu uygulamayı, kütüphane kilit açıcılarını ve üçüncü taraf eklentileri kullanırken karşılaşabileceğiniz her türlü hesap uyarısı, oyun içi kısıtlama veya olası yaptırımlar tamamen kullanıcının kendi sorumluluğundadır. SteaMRogue geliştiricileri ve katkıda bulunanları hiçbir hukuki, idari veya maddi sorumluluk kabul etmemektedir.",
            "disc_vac_title": "📌 Önemli Hatırlatma (VAC & Rekabetçi Oyunlar)",
            "disc_vac_text1": "Counter-Strike 2 (CS2), Dota 2 veya Team Fortress 2 gibi Valve Anti-Cheat (VAC) korumalı rekabetçi oyunlara girmeden önce mutlaka üst kısımdaki anahtardan Güvenli Mod'a geçiniz.",
            "disc_vac_text2": "SteaMRogue modunda unutup oyuna girilmesi durumunda anında kalıcı ban riski çok düşük olsa da Valve sunucuları \"VAC oyun oturumunuzu doğrulayamadı\" uyarısı vererek maçlara girişi engelleyebilir. Güvenli Mod, Steam'i %100 orijinal ve temiz haline getirerek oturum hatalarını ve tüm riskleri tamamen ortadan kaldırır.",
            "disc_countdown_text": "Şartları Okudum ve Kabul Ediyorum ({sec})",
            "disc_accept_ready": "Şartları Okudum ve Kabul Ediyorum",

            // --- SYSTEM NUKE CONFIRMATION MODAL ---
            "nuke_title": "DİKKAT: Sistemi İmha Etmek İstediğinize Emin Misiniz?",
            "nuke_subtitle": "Bu işlem geri alınamaz ve aşağıdaki adımların tümünü gerçekleştirecektir:",
            "nuke_item1_label": "Tüm Eklenen Oyunlar:",
            "nuke_item1_desc": "SteamTools ile Steam kütüphanenize eklenen tüm oyunların LUA dosyaları silinecektir.",
            "nuke_item2_label": "SteamTools Kancası:",
            "nuke_item2_desc": "Steam klasörüne yerleştirilen kilit açıcı DLL dosyaları (dwmapi.dll, OpenSteamTool.dll vb.) kaldırılacaktır.",
            "nuke_item3_label": "Bypass & Fix Dosyaları:",
            "nuke_item3_desc": "Oyun klasörlerine atılan tüm fixler silinecek ve orijinal dosyalar geri yüklenecektir.",
            "nuke_item4_label": "Uygulama ve Kısayollar:",
            "nuke_item4_desc": "SteaMRogue verileri, ayarları, önbelleği, masaüstü ve başlat menüsü kısayolları silinip uygulama tamamen kaldırılacaktır.",
            "nuke_info_box": "İmha işlemi başlatıldıktan sonra uygulama kapanacak ve temizlik arka planda kalıcı olarak tamamlanacaktır.",
            "nuke_btn_cancel": "İptal",
            "nuke_btn_confirm": "Evet, Her Şeyi İmha Et ve Kaldır",

            // --- HEALTH WARNING MODAL ---
            "health_title": "Sistem Sağlık Uyarısı",
            "health_issues_lead": "Açılış denetiminde aşağıdaki sorunlar tespit edildi:",
            "health_warning_box": "Steam'in çökmesini ve açılmama sorunlarını engellemek için sistemin onarılması gerekmektedir. Onarılsın mı?",
            "health_btn_repair": "Sistemi Onar",

            // --- GAME DETAILS MODAL ---
            "modal_details_title": "Oyun Detayları",
            "modal_badge_game": "OYUN",
            "modal_badge_age": "18+",
            "modal_badge_meta": "Metacritic: --",
            "modal_desc_loading": "Oyun açıklaması yükleniyor...",
            "modal_btn_play": "Oyunu Başlat",
            "modal_btn_delete": "Kütüphaneden Kaldır",
            "modal_btn_add": "Kütüphaneye Ekle",

            // --- UPDATER BANNER ---
            "updater_title": "Yeni Güncelleme Mevcut!",
            "updater_desc": "Güncelleme arka planda otomatik indiriliyor...",
            "updater_downloading": "İndiriliyor...",
            "updater_btn_later": "Daha Sonra",
            "updater_btn_restart": "Şimdi Güncelle & Yeniden Başlat",

            // --- FOOTER STATUS BAR ---
            "footer_steam_ready": "Steam Bağlantısı: Hazır",
            "footer_steam_running": "Steam Çalışıyor (PID: {pid})",
            "footer_steam_stopped": "Steam Kapalı",
            "footer_developer": "Geliştirici:",

            // --- TRANSITION & TOASTS ---
            "lang_switching_title": "Dil Değiştiriliyor...",
            "lang_switching_sub": "Arayüz ve kütüphane bileşenleri güncelleniyor...",
            "toast_lang_changed": "Dil Türkçe olarak ayarlandı.",
            "toast_game_added": "'{name}' başarıyla kütüphanenize eklendi!",
            "toast_game_add_error": "Oyun eklenemedi: {err}",
            "toast_steam_restarted": "Steam başarıyla yeniden başlatıldı!",
            "toast_steam_restart_error": "Steam yeniden başlatılamadı: {err}",
            "toast_mode_safe": "Güvenli Mod aktif. Steam orijinal ve temiz duruma getirildi.",
            "toast_mode_rogue": "SteaMRogue Modu aktif. Kütüphane kilit açıcıları çalışıyor.",
            "toast_game_removed": "'{name}' kütüphaneden kaldırıldı.",
            "toast_cache_cleared": "Steam indirme önbelleği başarıyla temizlendi.",
            "toast_copied": "Panoya kopyalandı!",
            "confirm_remove_game_msg": "'{name}' adlı oyunu kütüphanenizden kaldırmak istediğinize emin misiniz?",
            "confirm_restart_steam_msg": "Steam istemcisi güvenle yeniden başlatılacak. Devam edilsin mi?",
            "loading_processing": "İşlem yapılıyor...",
            "splash_status_done": "Sistem hazır, kütüphaneye bağlanıldı.",
            "splash_status_sync": "Kilit açıcılar ve manifest depoları eşitleniyor...",
            "splash_status_verify": "İmzalar ve bypass listesi doğrulanıyor...",
            "splash_subtitle": "Yeni Nesil Steam Kiti",
            "btn_ok": "Tamam",
            "btn_cancel": "İptal",
            "modal_confirm_title": "Onay Gerekli",
            "modal_alert_title": "SteaMRogue",
            "alert_game_failed_title": "Oyun Eklenemedi",
            "msg_no_community_manifest": "'{name}' (AppID: {appid}) için henüz topluluk dosyaları yayınlanmamış.\n\nEğer elinizde manifest dosyası var ise 'İçe Aktar' sekmesinden ekleyebilirsiniz.",

            // --- ONLINEFIX DYNAMIC TEXTS ---
            "of_badge_multiplayer": "Multiplayer Fix",
            "of_card_desc_gofile": "Gofile sunucusu üzerinden doğrudan indirme ve Steam otomatik entegrasyonu.",
            "of_btn_download_fix": "Fix İndir",
            "of_btn_visit_site": "Siteye Git",
            "of_btn_visit_title": "Varsayılan tarayıcınızda resmi sayfayı açın",
            "of_no_games": "Kütüphanenizde oyun bulunamadı.",

            // --- BYPASS DYNAMIC TEXTS ---
            "bp_note_default": "Bu oyun için özel bir not bulunmuyor. İyi oyunlar!",
            "bp_meta_yes": "Evet",
            "bp_meta_no": "Hayır",
            "bp_btn_apply_fix": "Fix Uygula",
            "bp_software_download_title": "{name} indirmek için tıkla",
            "bp_games_count": "{current} / {total} Oyun",

            // --- SAM ACHIEVEMENTS DYNAMIC TEXTS ---
            "ach_manage_btn": "Başarımları Yönet",
            "ach_manage_title": "Bu oyun için Steam Achievement Manager'ı başlat",
            "ach_loading_status": "Steam başarımları yükleniyor, lütfen bekleyin...",
            "ach_no_match_query": "Aramanızla Eşleşen Başarım Bulunamadı",
            "ach_no_achievements_for_game": "Bu Oyun İçin Başarım Bulunamadı",
            "ach_try_different_keyword": "Farklı bir anahtar kelime aramayı deneyin.",
            "ach_none_configured_for_game": "Bu oyunda Steam başarımı tanımlanmamış olabilir.",
            "ach_displayed_count": "Görüntülenen: {current} / {total}",
            "ach_load_failed_title": "Başarımlar Yüklenemedi",
            "ach_load_failed_desc": "Steam bağlantısı kurulamadı veya oyun kütüphanede doğrulanmadı.",
            "ach_retry_btn": "Yeniden Dene",
            "ach_connection_error": "Bağlantı Hatası",
            "ach_scanning_library": "Kütüphaneniz taranıyor...",
            "ach_scanning_library_sub": "Steam oyunlarınız ve başarımlar listeleniyor",
            "ach_empty_library": "Kütüphanenizde Henüz Oyun Bulunamadı",
            "ach_empty_library_sub": "Steam hesabınıza giriş yapıldığından ve kütüphanenizde oyun bulunduğundan emin olun.",
            "of_searching": "Aranıyor...",
            "of_searching_desc": "Online-fix.me üzerinde multiplayer yamalar aranıyor...",

            // --- SETTINGS DYNAMIC BADGES & TEXTS ---
            "set_btn_check_update": "Güncellemeleri Denetle",
            "set_btn_repair_install": "Son Sürümü Yeniden İndir / Onar",
            "set_update_latest": "Harika! Zaten en güncel sürümü ({ver}) kullanıyorsunuz.",
            "set_update_checking": "Güncellemeler denetleniyor...",
            "set_update_checking_desc": "GitHub üzerinden yeni sürüm kontrolü yapılıyor...",
            "set_sync_badge_running": "EŞİTLENİYOR...",
            "set_sync_badge_ready": "GÜNCEL",
            "set_sync_last_time": "Son Senkronizasyon: {time} (Tüm bileşenler ve kaynaklar aktif)",
            "set_sync_all_active": "Tüm depolar, kancalar ve manifest kaynakları aktif.",
            "set_st_dll_synced": "Eşitlendi (Aktif)",
            "set_st_dll_just_updated": "Yeni Güncellendi",
            "set_toml_sig_compat": "Dinamik Uyumlu",
            "set_repo_count_active": "{count} Aktif",
            "set_bypass_synced": "Çevrimiçi Eşit",
            "set_st_active_good": "AKTİF (HER ŞEY YOLUNDA)",
            "set_st_ready_closed": "HAZIR (STEAM KAPALI)",
            "set_st_passive_not_installed": "PASİF (KURULU DEĞİL)",
            "set_st_none": "Yok",
            "set_vc_installed_good": "KURULU (HER ŞEY YOLUNDA)",
            "set_vc_installed_good_text": "Microsoft Visual C++ (x86 & x64) paketleri sisteminizde eksiksiz kurulu, her şey yolunda.",
            "set_vc_missing": "EKSİK (YÜKLEME GEREKLİ)",
            "set_av_safe": "GÜVENLİ (SORUN YOK)",
            "set_av_safe_text": "Kilit açıcı kütüphaneler karantinaya alınmamış, yerinde duruyor. Her şey yolunda.",
            "set_av_detected_title": "{av} Kullandığınız Tespit Edildi:",
            "set_av_third_party_default": "Harici Antivirüs (Avast/Kaspersky vb.) Kullananlar İçin:",
            "footer_steam_conn": "Steam Bağlantısı: {path}",
            "footer_steam_not_found": "Steam Bulunamadı (Settings sekmesinden yolu belirleyin)",
            "lib_no_match": "Arama kriterlerinize uygun oyun bulunamadı."
        },

        en: {
            // --- HEADER & NAV ---
            "app_title": "SteaMRogue",
            "nav_library": "Library",
            "nav_onlinefix": "OnlineFix",
            "nav_bypass": "Bypass",
            "nav_deals": "Deals",
            "nav_achievements": "Achievements",
            "nav_import": "Import",
            "nav_settings": "Settings",
            "btn_minimize": "Minimize",
            "btn_maximize": "Maximize / Restore",
            "btn_close": "Close",
            "select_language": "Select Language / Dil Seçimi",

            // --- SUB-HEADER / ACTIONS & CLOCK ---
            "system_time": "SYSTEM TIME",
            "loading_clock": "Loading...",
            "btn_how_to": "How to Use?",
            "search_placeholder": "Enter Steam store link, AppID or game name (e.g. store.steampowered.com/app/...)...",
            "btn_add_to_library": "Add to Library",
            "btn_restart_steam": "Restart Steam",
            "btn_restart_steam_title": "Safely restarts the Steam client",
            "mode_safe": "Safe Mode",
            "mode_safe_title": "Unloads unlock hooks. 100% clean and safe for CS2 and VAC-secured titles.",
            "mode_steamrogue": "SteaMRogue Mode",
            "mode_steamrogue_title": "Unlocks Steam library features and activates games.",
            "mode_help_tooltip": "Information about Operational Modes and VAC Safety",
            "mode_restart_needed": "Restart Required",

            // --- LIBRARY TAB ---
            "lib_title": "Your Game Library",
            "lib_games_count": "{count} games",
            "lib_sort_newest": "Newest",
            "lib_sort_az": "A-Z",
            "lib_refresh": "Refresh",
            "lib_refresh_title": "Refresh Library",
            "lib_search_placeholder": "Search in library...",
            "lib_prev": "Previous",
            "lib_next": "Next",
            "lib_page_info": "Page {current}/{total}",
            "lib_empty_title": "No games added to your library yet.",
            "lib_empty_desc": "Use the search bar above to add any game link, numeric AppID or title.",
            "badge_installed": "INSTALLED",
            "badge_downloadable": "DOWNLOADABLE",
            "ctx_launch_game": "Launch Game",
            "ctx_browse_files": "Open File Location",
            "ctx_open_in_steam": "View on Steam",
            "ctx_manage_achievements": "Manage Achievements",
            "ctx_check_onlinefix": "Check OnlineFix Patch",
            "ctx_remove_game": "Remove from Library",

            // --- DEALS TAB ---
            "deals_title": "Special Deals & Discounts",
            "deals_badge": "Steam Specials",
            "deals_refresh": "Refresh",
            "deals_search_placeholder": "Search discounted games (e.g. Witcher, Cyberpunk)...",
            "deals_clear_search": "Clear Search",
            "deals_notice_note": "Note:",
            "deals_notice_text": "Game categories are filtered directly from Steam data; minor classification anomalies may occur.",
            "deals_genre_label": "Genre:",
            "deals_genre_all": "All",
            "deals_genre_action": "Action",
            "deals_genre_adventure": "Adventure",
            "deals_genre_rpg": "RPG",
            "deals_genre_strategy": "Strategy",
            "deals_genre_simulation": "Simulation",
            "deals_genre_sports": "Sports",
            "deals_genre_indie": "Indie",
            "deals_discount_label": "Discount:",
            "deals_max_price_label": "Max Price:",
            "deals_loading": "Loading active Steam discounts...",

            // --- ACHIEVEMENTS TAB (SAM) ---
            "ach_title": "Achievements (SAM)",
            "ach_subtitle_tag": "Steam Achievement Manager",
            "ach_desc": "View and manage achievements for games associated with your Steam account.",
            "ach_library_games_label": "Games in Library:",
            "ach_btn_refresh": "Refresh",
            "ach_btn_refresh_title": "Rescan Library",
            "ach_search_placeholder": "Search your library games or enter AppID (e.g. Counter-Strike, Cyberpunk, 730)...",
            "ach_scanning_title": "Scanning library...",
            "ach_scanning_desc": "Indexing Steam games and achievement rosters",
            "ach_modal_title": "Game Achievements",
            "ach_modal_unlocked": "Unlocked:",
            "ach_modal_rate": "Completion Rate:",
            "ach_btn_unlock_all": "Unlock All",
            "ach_btn_lock_all": "Lock All",
            "ach_btn_invert": "Invert",
            "ach_modal_search_placeholder": "Search achievement...",
            "ach_btn_save_steam": "Save to Steam",
            "ach_modal_status_hint": "Click 'Save to Steam' to commit and synchronize your changes.",

            // --- IMPORT TAB ---
            "imp_title": "Import Files",
            "imp_desc": "Effortlessly import downloaded Steam manifests (.manifest), unlock configuration scripts (.lua), or zip archives (.zip) into Steam.",
            "imp_drop_title": "Drag & Drop Files Here",
            "imp_drop_sub": "Supported formats: .lua, .zip, .manifest",
            "imp_btn_browse": "Browse Files",
            "imp_how_to_use": "How to Use:",
            "imp_rule_manifest": ".manifest files: Automatically places the depot manifest into the appropriate Steam depot directory.",
            "imp_rule_lua": ".lua files: Copies unlock scripts straight into your Steam configuration folder.",
            "imp_rule_zip": ".zip archives: Automatically extracts packages into their respective target Steam directories.",

            // --- SETTINGS TAB ---
            "set_main_title": "Application Settings & System Management",
            "set_main_desc": "Manage Steam unlock engines, auto-updates, library self-healing, and security integrations.",
            "set_app_update_title": "SteaMRogue Application Update",
            "set_app_update_desc": "Updates automatically via GitHub Releases. You can check for updates or repair your installation anytime.",
            "set_app_update_status": "Auto-update engine is active.",
            "set_btn_check_update": "Check for Updates",
            "set_btn_repair_install": "Redownload Latest Version / Repair",
            "set_sync_title": "Component, Manifest & Signature Sync (Live Engine)",
            "set_sync_badge": "UP TO DATE",
            "set_sync_desc": "SteamTools hooks, OpenSteamTool TOML signatures, community manifest databases, OnlineFix bypasses, and game Lua scripts synchronize automatically in the background.",
            "set_sync_status": "All repositories, hooks, and manifest sources are active.",
            "set_btn_sync_now": "Sync Components & Signatures Now",
            "set_st_dll_label": "SteamTools DLL:",
            "set_st_dll_status": "Synced",
            "set_toml_sig_label": "TOML Signatures:",
            "set_toml_sig_status": "Dynamically Matched",
            "set_manifest_repo_label": "Manifest Repos:",
            "set_manifest_repo_status": "4/4 Active",
            "set_of_bypass_label": "OnlineFix Bypass:",
            "set_of_bypass_status": "Online Synced",

            "set_steam_dir_title": "Steam Installation Directory",
            "set_steam_dir_helper": "Automatically detected from Windows Registry if left blank.",
            "set_btn_save_dir": "Save Directory",

            "set_self_heal_title": "Self-Healing Engine",
            "set_self_heal_badge": "HEALTHY",
            "set_self_heal_desc": "SteaMRogue routinely scans and repairs Steam unlock hooks, LUA configurations, Spacewar (480) multiplayer registries, 7-Zip binaries, and corrupted caches on startup.",
            "set_self_heal_status": "All components, hooks, and services are fully verified and active.",
            "set_btn_self_heal": "Auto-Scan and Repair System",

            "set_st_hook_title": "SteamTools Hook (OpenSteamTool)",
            "set_st_hook_desc": "Deploys necessary unlock DLLs (dwmapi.dll, xinput1_4.dll, OpenSteamTool.dll) into the Steam root folder.",
            "set_hook_status_label": "Hook Status:",
            "set_hook_status_active": "ACTIVE (ALL GOOD)",
            "set_detected_files_label": "Detected Files:",
            "set_none": "None",
            "set_btn_install_st": "Install / Repair SteamTools",
            "set_btn_restart_steam_st": "Restart Steam",
            "set_btn_clear_cache_st": "Clear Download Cache (Fixes \"No Internet\")",
            "set_btn_uninstall_st": "Uninstall SteamTools",

            "set_vcredist_title": "System Dependencies (Microsoft Visual C++ 2015-2022)",
            "set_vcredist_badge": "INSTALLED (ALL GOOD)",
            "set_vcredist_desc": "Both 32-bit (x86) and 64-bit (x64) Visual C++ runtimes are essential to prevent game crashes and support SteamTools and OnlineFix multiplayer modules.",
            "set_vcredist_status": "Microsoft Visual C++ (x86 & x64) is fully installed on your system.",
            "set_btn_install_vcredist": "Download & Install Missing Runtimes",

            "set_av_title": "Antivirus & Protection Settings (Quarantine Prevention)",
            "set_av_badge": "SECURE (NO ISSUES)",
            "set_av_desc": "Prevent SteaMRogue and SteamTools components from being quarantined or deleted as false positives by Windows Defender or third-party suites.",
            "set_av_status": "Unlock libraries are intact and not quarantined. Everything is running smoothly.",
            "set_btn_restore_quarantine": "Recover from Quarantine & Repair",
            "set_btn_add_defender_exclusion": "Add Windows Defender Exclusion",
            "set_external_av_title": "For Third-Party Antivirus Users (Avast, Kaspersky, etc.):",
            "set_external_av_desc": "Simply add your Steam and SteaMRogue install folders to your antivirus Exclusions / Exceptions list.",
            "set_btn_copy_exclusion_paths": "Copy Exclusion Paths",

            "set_disclaimer_title": "Legal Notice & User Responsibility Agreement",
            "set_disclaimer_desc": "Revisit the initial legal disclaimer, VAC protection guidelines, and terms of service at any time.",
            "set_btn_view_disclaimer": "View Agreement",

            "set_danger_title": "Danger Zone: Complete System Self-Destruct",
            "set_danger_desc": "Uninstalls SteamTools hooks, wipes imported manifests and LUA configurations, removes all applied bypass fix files, and uninstalls SteaMRogue completely.",
            "set_btn_nuke": "Completely Wipe & Uninstall System",

            // --- ONLINEFIX TAB ---
            "of_title": "OnlineFix Multiplayer Patches",
            "of_rar_pw_label": "Archive password:",
            "of_search_placeholder": "Search patch (e.g. Palworld, Ready or Not)...",
            "of_btn_search": "Search",
            "of_info_title": "Important Information & Notes",
            "of_note1_title": "Antivirus & Protection Guidelines",
            "of_note1_text": "To ensure patches integrate smoothly and games start properly, temporarily toggle off Windows Security > Real-time protection (and any third-party antivirus). Otherwise, Windows may delete the patch files. (You only need it off while launching and playing; turn it back on once finished.)",
            "of_note2_title": "Multiplayer / Matchmaking Note",
            "of_note2_text": "Online-Fix patched games can only match with other players using the same patch. You cannot match with legitimate retail copies. Friends you play with must also install the patch.",
            "of_dl_heading": "Downloading Multiplayer Patch",
            "of_dl_file_loading": "File: Resolving download links...",
            "of_dl_starting": "Starting download...",
            "of_btn_open_download": "Open Downloaded File",
            "of_btn_cancel_download": "Cancel",
            "of_search_prompt": "Use the search box above to find multiplayer patches on OnlineFix.",
            "of_library_games_title": "Library Games",

            // --- BYPASS TAB ---
            "bp_search_placeholder": "Search games in this category...",
            "bp_loading_games": "Loading game list and artwork...",
            "bp_btn_back": "Back to Game List",
            "bp_label_notes": "Installation & Usage Notes",
            "bp_label_known_issues": "Known Issues & Fixes",
            "bp_label_software": "Required Additional Software",
            "bp_label_config": "Game Configuration",
            "bp_key_appid": "App ID",
            "bp_key_direct_exe": "Direct Launch via EXE",
            "bp_key_steam_launch": "Launch via Steam",
            "bp_key_fix_type": "Fix Type",
            "bp_btn_apply_fix": "Apply Fix",

            // --- BYPASS CHOICE MODAL ---
            "bp_modal_choice_title": "Bypass Fix Installation Option",
            "bp_modal_choice_desc": "Please choose how you would like to apply the fix files:",
            "bp_opt_auto_title": "Auto Detect & Install",
            "bp_opt_auto_badge": "Recommended",
            "bp_opt_auto_desc": "Scans Steam libraries across all storage drives (C:, D:, E: etc.), finds the game directory, and applies the fix automatically.",
            "bp_opt_manual_title": "Select Folder Manually",
            "bp_opt_manual_desc": "Automatically opens your Steam library (steamapps\\common) so you can pick the game folder yourself.",
            "bp_choice_warning": "If automatic detection cannot locate your game or if it is not installed yet, no files will be modified and the manual selector will open safely.",
            "bp_btn_cancel": "Cancel",

            // --- DEFENDER WARNING MODAL ---
            "def_modal_title": "Windows Defender Notice",
            "def_modal_body": "Before applying this fix, add the game installation folder to your Windows Defender exclusions list. Otherwise, the patch may be blocked.",
            "def_modal_question": "Have you added the game folder to exclusions?",
            "def_btn_no": "No",
            "def_btn_yes": "Yes, Continue",

            // --- ONLINEFIX CHOICE MODAL ---
            "of_modal_choice_title": "OnlineFix Patch Installation Option",
            "of_modal_choice_desc": "Please choose where you would like the multiplayer patch applied:",
            "of_opt_desktop_title": "Download to Desktop",
            "of_opt_desktop_desc": "Downloads the archive to your Desktop only. You will need to extract and install it manually.",
            "of_opt_integrate_title": "Integrate into Game",
            "of_opt_integrate_badge": "Recommended",
            "of_opt_integrate_desc": "Downloads, extracts using the archive password (online-fix.me), injects into the game directory, and cleans up temporary archives.",
            "of_choice_warning_title": "Important Note:",
            "of_choice_warning_text": "The \"Integrate into Game\" option requires the game to be installed on your computer. Otherwise, the operation will fail or damage file structures!",
            "of_btn_cancel": "Cancel",

            // --- HOW TO USE GUIDE MODAL ---
            "guide_modal_title": "How to Add Games?",
            "guide_step1_title": "Enter Game Link, AppID or Name",
            "guide_step1_desc": "Type or paste the Steam store URL, numeric AppID, or game title into the top search box (e.g. https://store.steampowered.com/app/477160 or 477160).",
            "guide_step2_title": "Click Add to Library",
            "guide_step2_desc": "Click \"Add to Library\". SteaMRogue registers the game license to your client in seconds.",
            "guide_step3_title": "Restart Steam",
            "guide_step3_desc": "Click \"Restart Steam\". Once Steam launches, your game will appear in your library ready for installation!",
            "guide_btn_confirm": "Got It",

            // --- MODE INFO GUIDE MODAL ---
            "mode_modal_title": "SteaMRogue Operational Modes Guide",
            "mode_safe_heading": "🛡️ Safe Mode",
            "mode_safe_desc": "Background SteamTools and game injection services are completely stopped. Games previously added to your library are never locked, never lost, and never display 'Purchase' prompts; they remain fully playable. Only new game addition hooks are paused.",
            "mode_safe_foot": "🛡️ Your games remain preserved in your library and SteamTools does not run in the background.",
            "mode_rogue_heading": "⚡ SteaMRogue Mode",
            "mode_rogue_desc": "SteamTools and library injection engines run actively. Add any game or DLC to your library with a single click, then download and play directly through Steam.",
            "mode_rogue_foot": "⚡ Use this mode when adding new games and expanding your library.",
            "mode_switch_heading": "🔄 Instant Switching with Zero Downtime",
            "mode_switch_desc": "Switch modes instantly with one click using the toggle in the top bar or via the Windows taskbar / system tray right-click menu.",
            "mode_btn_confirm": "Got It",

            // --- DISCLAIMER & EULA MODAL (10s) ---
            "disc_header_title": "Legal Notice & User Responsibility Agreement",
            "disc_lead": "SteaMRogue is an open-source companion software that provides local library management and independent tool orchestration.",
            "disc_main_text": "Any account warnings, in-game restrictions, or potential sanctions encountered while utilizing this software, library unlock tools, or third-party plugins remain solely the user's responsibility. The creators and contributors of SteaMRogue assume no legal, administrative, or financial liability.",
            "disc_vac_title": "📌 Important Reminder (VAC & Competitive Titles)",
            "disc_vac_text1": "Before launching Valve Anti-Cheat (VAC) protected titles such as Counter-Strike 2 (CS2), Dota 2, or Team Fortress 2, always switch to Safe Mode using the toggle above.",
            "disc_vac_text2": "While accidental launches in SteaMRogue mode carry a very low immediate permanent ban risk, Valve matchmaking servers may block entry with a \"VAC was unable to verify your game session\" prompt. Safe Mode restores Steam to 100% clean vanilla status, eliminating session mismatches and all associated risks.",
            "disc_countdown_text": "I Have Read & Agree to the Terms ({sec})",
            "disc_accept_ready": "I Have Read & Agree to the Terms",

            // --- SYSTEM NUKE CONFIRMATION MODAL ---
            "nuke_title": "CAUTION: Are You Sure You Want to Destroy the System?",
            "nuke_subtitle": "This action cannot be undone and will perform every single step below:",
            "nuke_item1_label": "All Added Games:",
            "nuke_item1_desc": "All LUA unlock files for games added to Steam via SteamTools will be permanently deleted.",
            "nuke_item2_label": "SteamTools Hook:",
            "nuke_item2_desc": "Unlock DLL files (dwmapi.dll, OpenSteamTool.dll, etc.) deployed into the Steam directory will be removed.",
            "nuke_item3_label": "Bypass & Fix Files:",
            "nuke_item3_desc": "All patches and fix files injected into game directories will be removed, restoring original files.",
            "nuke_item4_label": "Application & Shortcuts:",
            "nuke_item4_desc": "SteaMRogue user data, settings, caches, and desktop/start menu shortcuts will be erased, uninstalling the app entirely.",
            "nuke_info_box": "Once triggered, the app will exit immediately while background cleanup finishes completely.",
            "nuke_btn_cancel": "Cancel",
            "nuke_btn_confirm": "Yes, Destroy Everything & Uninstall",

            // --- HEALTH WARNING MODAL ---
            "health_title": "System Health Alert",
            "health_issues_lead": "The startup audit detected the following issues:",
            "health_warning_box": "To prevent Steam crashes and launch failures, system components must be repaired. Proceed with repair?",
            "health_btn_repair": "Repair System",

            // --- GAME DETAILS MODAL ---
            "modal_details_title": "Game Details",
            "modal_badge_game": "GAME",
            "modal_badge_age": "18+",
            "modal_badge_meta": "Metacritic: --",
            "modal_desc_loading": "Loading game description...",
            "modal_btn_play": "Launch Game",
            "modal_btn_delete": "Remove from Library",
            "modal_btn_add": "Add to Library",

            // --- UPDATER BANNER ---
            "updater_title": "New Update Available!",
            "updater_desc": "Update is being downloaded automatically in the background...",
            "updater_downloading": "Downloading...",
            "updater_btn_later": "Later",
            "updater_btn_restart": "Update & Restart Now",

            // --- FOOTER STATUS BAR ---
            "footer_steam_ready": "Steam Connection: Ready",
            "footer_steam_running": "Steam Running (PID: {pid})",
            "footer_steam_stopped": "Steam Stopped",
            "footer_developer": "Developer:",

            // --- TRANSITION & TOASTS ---
            "lang_switching_title": "Switching Language...",
            "lang_switching_sub": "Updating interface and library components...",
            "toast_lang_changed": "Language set to English.",
            "toast_game_added": "'{name}' added to your library successfully!",
            "toast_game_add_error": "Could not add game: {err}",
            "toast_steam_restarted": "Steam restarted successfully!",
            "toast_steam_restart_error": "Could not restart Steam: {err}",
            "toast_mode_safe": "Safe Mode active. Steam restored to clean vanilla state.",
            "toast_mode_rogue": "SteaMRogue Mode active. Library unlock engines running.",
            "toast_game_removed": "'{name}' removed from your library.",
            "toast_cache_cleared": "Steam download cache cleared successfully.",
            "toast_copied": "Copied to clipboard!",
            "confirm_remove_game_msg": "Are you sure you want to remove '{name}' from your library?",
            "confirm_restart_steam_msg": "Steam client will safely restart. Continue?",
            "loading_processing": "Processing...",
            "splash_status_done": "System ready, connected to library.",
            "splash_status_sync": "Synchronizing unlockers and manifest repositories...",
            "splash_status_verify": "Verifying signatures and bypass manifests...",
            "splash_subtitle": "Next-Gen Steam Toolkit",
            "btn_ok": "OK",
            "btn_cancel": "Cancel",
            "modal_confirm_title": "Confirmation Required",
            "modal_alert_title": "SteaMRogue",
            "alert_game_failed_title": "Failed to Add Game",
            "msg_no_community_manifest": "No community files have been published for '{name}' (AppID: {appid}) yet.\n\nIf you have the manifest file, you can add it via the 'Import' tab.",

            // --- ONLINEFIX DYNAMIC TEXTS ---
            "of_badge_multiplayer": "Multiplayer Fix",
            "of_card_desc_gofile": "Direct download via Gofile and automated Steam integration.",
            "of_btn_download_fix": "Download Fix",
            "of_btn_visit_site": "Visit Site",
            "of_btn_visit_title": "Open official page in your default browser",
            "of_no_games": "No games found in your library.",

            // --- BYPASS DYNAMIC TEXTS ---
            "bp_note_default": "No special notes for this game. Have fun!",
            "bp_meta_yes": "Yes",
            "bp_meta_no": "No",
            "bp_btn_apply_fix": "Apply Fix",
            "bp_software_download_title": "Click to download {name}",
            "bp_games_count": "{current} / {total} Games",

            // --- SAM ACHIEVEMENTS DYNAMIC TEXTS ---
            "ach_manage_btn": "Manage Achievements",
            "ach_manage_title": "Launch Steam Achievement Manager for this title",
            "ach_loading_status": "Loading Steam achievements, please wait...",
            "ach_no_match_query": "No Achievements Found Matching Your Query",
            "ach_no_achievements_for_game": "No Achievements Found for This Game",
            "ach_try_different_keyword": "Try searching with a different keyword.",
            "ach_none_configured_for_game": "Steam achievements may not be configured for this title.",
            "ach_displayed_count": "Displayed: {current} / {total}",
            "ach_load_failed_title": "Achievements Could Not Be Loaded",
            "ach_load_failed_desc": "Could not connect to Steam or title is not verified in library.",
            "ach_retry_btn": "Try Again",
            "ach_connection_error": "Connection Error",
            "ach_scanning_library": "Scanning your library...",
            "ach_scanning_library_sub": "Listing your Steam titles and achievements",
            "ach_empty_library": "No Titles Found in Your Library Yet",
            "ach_empty_library_sub": "Make sure you are logged into your Steam client and have titles in your library.",
            "of_searching": "Searching...",
            "of_searching_desc": "Searching multiplayer fixes on Online-fix.me...",

            // --- SETTINGS DYNAMIC BADGES & TEXTS ---
            "set_btn_check_update": "Check for Updates",
            "set_btn_repair_install": "Redownload Latest Version / Repair",
            "set_update_latest": "Great! You are already using the latest version ({ver}).",
            "set_update_checking": "Checking for updates...",
            "set_update_checking_desc": "Checking GitHub for new releases...",
            "set_sync_badge_running": "SYNCING...",
            "set_sync_badge_ready": "UP TO DATE",
            "set_sync_last_time": "Last Sync: {time} (All components and sources active)",
            "set_sync_all_active": "All repositories, hooks, and manifest sources active.",
            "set_st_dll_synced": "Synced (Active)",
            "set_st_dll_just_updated": "Recently Updated",
            "set_toml_sig_compat": "Dynamically Compatible",
            "set_repo_count_active": "{count} Active",
            "set_bypass_synced": "Online Synced",
            "set_st_active_good": "ACTIVE (ALL GOOD)",
            "set_st_ready_closed": "READY (STEAM CLOSED)",
            "set_st_passive_not_installed": "INACTIVE (NOT INSTALLED)",
            "set_st_none": "None",
            "set_vc_installed_good": "INSTALLED (ALL GOOD)",
            "set_vc_installed_good_text": "Microsoft Visual C++ (x86 & x64) runtimes are fully installed on your system, all good.",
            "set_vc_missing": "MISSING (INSTALLATION REQUIRED)",
            "set_av_safe": "SAFE (NO ISSUES)",
            "set_av_safe_text": "Unlocker libraries are not quarantined and present in place. All good.",
            "set_av_detected_title": "{av} Detected on Your System:",
            "set_av_third_party_default": "For Users with Third-Party Antivirus (Avast/Kaspersky etc.):",
            "footer_steam_conn": "Steam Connection: {path}",
            "footer_steam_not_found": "Steam Not Found (Specify path in Settings tab)",
            "lib_no_match": "No games found matching your search criteria."
        }
    };

    // Current active language (default: 'tr')
    let currentLang = "tr";

    // Translation function
    function t(key, params = {}) {
        const dict = translations[currentLang] || translations["tr"];
        let text = dict[key] !== undefined ? dict[key] : (translations["tr"][key] !== undefined ? translations["tr"][key] : key);

        for (const [k, v] of Object.entries(params)) {
            text = text.replace(new RegExp(`\\{${k}\\}`, "g"), v);
        }
        return text;
    }

    // Circular High-Fidelity SVG Flags (Rendering 100% reliably on all Windows versions)
    const FLAG_TR_SVG = `<svg viewBox="0 0 32 32" width="100%" height="100%" style="border-radius:50%;overflow:hidden;display:block;">
        <circle cx="16" cy="16" r="16" fill="#E30A17"/>
        <circle cx="14" cy="16" r="7.5" fill="#FFFFFF"/>
        <circle cx="16.5" cy="16" r="6" fill="#E30A17"/>
        <polygon points="19.5,13.2 20.4,15.2 22.5,15.2 20.8,16.5 21.4,18.5 19.5,17.2 17.6,18.5 18.2,16.5 16.5,15.2 18.6,15.2" fill="#FFFFFF" transform="rotate(-18 19.5 16)"/>
    </svg>`;

    const FLAG_EN_SVG = `<svg viewBox="0 0 32 32" width="100%" height="100%" style="border-radius:50%;overflow:hidden;display:block;">
        <rect width="32" height="32" fill="#012169"/>
        <path d="M0,0 L32,32 M32,0 L0,32" stroke="#FFFFFF" stroke-width="6.5"/>
        <path d="M0,0 L32,32 M32,0 L0,32" stroke="#C8102E" stroke-width="3.5"/>
        <path d="M16,0 V32 M0,16 H32" stroke="#FFFFFF" stroke-width="9.5"/>
        <path d="M16,0 V32 M0,16 H32" stroke="#C8102E" stroke-width="5.5"/>
    </svg>`;

    function getFlagSvg(lang) {
        return lang === "en" ? FLAG_EN_SVG : FLAG_TR_SVG;
    }

    // Apply translations across all DOM elements
    function updateDOMTranslations() {
        // 1. Text elements
        document.querySelectorAll("[data-i18n]").forEach((el) => {
            const key = el.getAttribute("data-i18n");
            if (key) {
                // If element has leading/trailing icons or badges that shouldn't be erased, preserve icon
                const icon = el.querySelector("i.fa-solid, i.fa-brands, i.fa-regular, span.live-dot");
                const badge = el.querySelector("span.badge, span.choice-badge-recommended");
                
                if (icon || badge) {
                    // Specific button with icon
                    const iconClone = icon ? icon.cloneNode(true) : null;
                    const badgeClone = badge ? badge.cloneNode(true) : null;
                    
                    el.innerHTML = "";
                    if (iconClone) el.appendChild(iconClone);
                    el.appendChild(document.createTextNode(" " + t(key) + " "));
                    if (badgeClone) el.appendChild(badgeClone);
                } else {
                    el.textContent = t(key);
                }
            }
        });

        // 2. Placeholder attributes
        document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
            const key = el.getAttribute("data-i18n-placeholder");
            if (key) el.placeholder = t(key);
        });

        // 3. Title / Tooltip attributes
        document.querySelectorAll("[data-i18n-title]").forEach((el) => {
            const key = el.getAttribute("data-i18n-title");
            if (key) el.title = t(key);
        });

        // 4. Update Flag Icon and Active states
        const flagEl = document.getElementById("lang-current-flag");
        const codeEl = document.getElementById("lang-current-code");
        if (flagEl) {
            flagEl.innerHTML = getFlagSvg(currentLang);
        }
        if (codeEl) {
            codeEl.textContent = currentLang === "en" ? "EN" : "TR";
        }

        const iconTr = document.getElementById("lang-icon-tr");
        const iconEn = document.getElementById("lang-icon-en");
        if (iconTr) iconTr.innerHTML = FLAG_TR_SVG;
        if (iconEn) iconEn.innerHTML = FLAG_EN_SVG;

        const optTr = document.getElementById("lang-opt-tr");
        const optEn = document.getElementById("lang-opt-en");
        if (optTr && optEn) {
            if (currentLang === "en") {
                optTr.classList.remove("active");
                optEn.classList.add("active");
            } else {
                optTr.classList.add("active");
                optEn.classList.remove("active");
            }
        }

        // 5. Update HTML lang attribute
        document.documentElement.lang = currentLang;

        // 6. Refresh active dynamic texts in script.js if hook exists
        if (window.refreshDynamicTranslations) {
            window.refreshDynamicTranslations();
        }
    }

    // Language switcher with smooth cyberpunk animation
    function setLanguage(lang, showTransition = true) {
        if (!translations[lang]) return;
        const prevLang = currentLang;
        currentLang = lang;

        // Persist language choice in localStorage
        try {
            localStorage.setItem("steamrogue_language", lang);
        } catch (e) {
            console.warn("Could not save language to localStorage:", e);
        }

        // Notify backend to persist in config
        try {
            fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ language: lang })
            }).catch(() => {});
        } catch (e) {}

        // Notify Electron System Tray menu
        try {
            if (window.electronAPI && typeof window.electronAPI.setLanguageForTray === 'function') {
                window.electronAPI.setLanguageForTray(lang);
            }
        } catch (e) {}

        if (showTransition) {
            const overlay = document.getElementById("lang-transition-overlay");
            const progressBar = document.getElementById("lang-progress-bar");
            const flagFrom = document.getElementById("trans-flag-from");
            const flagTo = document.getElementById("trans-flag-to");
            const titleEl = document.getElementById("trans-title");
            const subEl = document.getElementById("trans-sub");

            if (overlay && progressBar) {
                if (flagFrom && flagTo) {
                    flagFrom.innerHTML = getFlagSvg(prevLang);
                    flagTo.innerHTML = getFlagSvg(lang);
                }
                if (titleEl) titleEl.textContent = t("lang_switching_title");
                if (subEl) subEl.textContent = t("lang_switching_sub");

                progressBar.style.width = "0%";
                overlay.classList.add("active");

                setTimeout(() => {
                    progressBar.style.width = "65%";
                }, 150);

                setTimeout(() => {
                    progressBar.style.width = "100%";
                    updateDOMTranslations();
                }, 400);

                setTimeout(() => {
                    overlay.classList.remove("active");
                    if (window.showToast) {
                        window.showToast(t("toast_lang_changed"), "success");
                    }
                }, 750);
                return;
            }
        }

        // Fallback instant update
        updateDOMTranslations();
    }

    // Initialize Language Engine
    function initI18n() {
        let saved = "tr"; // Strict default: Turkish for initial launch
        try {
            saved = localStorage.getItem("steamrogue_language");
            if (!saved || (saved !== "tr" && saved !== "en")) {
                saved = "tr";
                localStorage.setItem("steamrogue_language", "tr");
            }
        } catch (e) {
            saved = "tr";
        }

        currentLang = saved;

        // Sync with Electron System Tray immediately
        try {
            if (window.electronAPI && typeof window.electronAPI.setLanguageForTray === 'function') {
                window.electronAPI.setLanguageForTray(currentLang);
            }
        } catch (e) {}

        // Bind language toggle button & dropdown
        const toggleBtn = document.getElementById("lang-toggle-btn");
        const menu = document.getElementById("lang-dropdown-menu");
        const optTr = document.getElementById("lang-opt-tr");
        const optEn = document.getElementById("lang-opt-en");

        if (toggleBtn && menu) {
            toggleBtn.onclick = (e) => {
                e.stopPropagation();
                menu.classList.toggle("active");
            };

            if (optTr) {
                optTr.onclick = (e) => {
                    e.stopPropagation();
                    menu.classList.remove("active");
                    setLanguage("tr", true);
                };
            }

            if (optEn) {
                optEn.onclick = (e) => {
                    e.stopPropagation();
                    menu.classList.remove("active");
                    setLanguage("en", true);
                };
            }

            document.addEventListener("click", (e) => {
                if (!menu.contains(e.target) && e.target !== toggleBtn) {
                    menu.classList.remove("active");
                }
            });
        }

        // Apply immediately
        updateDOMTranslations();
    }

    // Expose Global i18n API
    window.i18n = {
        t,
        setLanguage,
        getCurrentLanguage: () => currentLang,
        initI18n,
        updateDOMTranslations
    };
    window.t = t;

    // Run automatically on DOM ready
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initI18n);
    } else {
        initI18n();
    }
})();
