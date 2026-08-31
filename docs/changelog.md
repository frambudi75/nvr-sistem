# Changelog - Python NVR System

Semua perubahan signifikan pada proyek ini didokumentasikan di berkas ini.

Format berkas ini mengikuti prinsip [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v1.5.0] - 2026-08-31
### Ditambahkan
* **Progressive Web App (PWA) Mobile Support:** Web App Manifest dan Service Worker agar dashboard NVR dapat diinstal langsung di layar beranda ponsel Android dan iOS.
* **Quick Siren Alarm (Web Audio API):** Tombol sirene darurat satu klik dengan synthesizer suara alarm berdenyut yang kencang tanpa memerlukan file audio eksternal.
* **Low-Latency Streaming & Audio Support (HLS Engine):** Dukungan pemutar HLS modern (`hls.js`) dengan audio pass-through langsung dari mikrofon kamera CCTV ke browser.
* **Interactive Floor Plan (Denah Interaktif):** Fitur unggah gambar denah rumah/gedung dan meletakkan pin kamera interaktif dengan live status dan klik untuk preview seketika.
* **Camera Area / Location Grouping:** Pengelompokan kamera berdasarkan lokasi (misal: *Outdoor, Lantai 1, Gudang*) dengan filter instan di dashboard.
* **Remote Backup & NAS Cloud Sync:** Pencadangan otomatis dan manual ke Telegram Channel (snapshot harian) serta folder penyimpanan sekunder (NAS/SMB).
* **Toggle AI Detection per Kamera:** Kontrol individual untuk mengaktifkan atau menonaktifkan proses AI deteksi manusia dan notifikasi per kamera.
* **AI Event Markers di Timeline Playback:** Garis penanda kuning/oranye interaktif di atas timeline 24 jam pada detik saat terdeteksi manusia/gerakan, lengkap dengan sidebar daftar event yang dapat diklik untuk langsung loncat (*seek*) ke momen kejadian tanpa menebak-nebak.
* **Pembersihan Penyimpanan Manual:** Opsi penghapusan rekaman berdasarkan umur hari, per kamera, snapshot AI, dan per tanggal rekaman di pemutar video.

---

## [v1.4.0] - 2026-08-15
### Ditambahkan
* **Fail-Safe Mechanism pada NVR Engine:** Pembungkusan modul AI (`AIDetector`) dalam penanganan error fleksibel agar kegagalan library Computer Vision tidak menggagalkan fungsi utama perekam dan web dashboard.
* **Pinning Versi Dependensi Stabil:** Mengunci `opencv-python-headless==4.9.0.80` dan `numpy<2` untuk mencegah *binary incompatibility crash* pada rilis NumPy 2.x.
* **Instalasi Pustaka Sistem OS:** Penambahan `libglib2.0-0` di Dockerfile untuk kompatibilitas runtime C++ OpenCV.
* **Dokumentasi Lengkap Proyek:** Penambahan folder `docs/` dengan spesifikasi arsitektur, PRD, database, REST API, UI/UX, deployment, dan changelog.

### Diperbaiki
* Mengatasi masalah *crash loop / Restarting* pada kontainer `python-nvr`.
* Menghilangkan alert pop-up pemblokir UI pada browser saat memutar file berkodek lawas, digantikan dengan *Graceful Soft Overlay*.

---

## [v1.3.0] - 2026-08-15
### Ditambahkan
* **AI Human Detection:** Deteksi keberadaan manusia di background menggunakan algoritma `cv2.HOGDescriptor`.
* **Discord Snapshot Alert:** Pengiriman notifikasi gambar langsung ke Discord Webhook dengan penanda kotak hijau deteksi (*bounding box*).
* **Video Clip Exporter:** Fitur pemotongan rekaman video dengan rentang waktu kustom (Start & End) dan fitur *Time-Lapse* (20x Fast Forward) langsung menjadi file MP4.
* **Digital Zoom & Pan:** Interaksi mouse wheel zoom (1x-5x) dan drag-to-pan pada pemutar video rekaman dan live view.

---

## [v1.2.0] - 2026-08-14
### Ditambahkan
* **Role-Based Access Control (RBAC):** Pemisahan hak akses antara akun `Admin` (akses penuh sistem & konfigurasi) dan `Viewer` (hanya pantau & playback).
* **Proteksi Endpoint API:** Dekorator `@admin_required` pada endpoint sensitif konfigurasi, manajemen user, dan jadwal.
* **Manajemen Pengguna di UI:** Tab *User & Security* untuk mengubah kata sandi akun Admin dan Viewer secara langsung.

---

## [v1.1.0] - 2026-08-14
### Ditambahkan
* **Web Dashboard Terpadu:** Antarmuka responsif dark mode berbasis Flask + Jinja2 pada port 5000.
* **Visual 24-Hour Timeline Scrubber:** Penjelajah rekaman harian dengan track segmen warna-warni dan tooltip waktu interaktif.
* **MJPEG Live Stream & PTZ Controller:** Streaming langsung dengan latensi rendah dan kontrol arah kamera.
* **System Monitor:** Visualisasi penggunaan CPU, Memori, dan Ruang Penyimpanan Disk secara real-time.
* **Log Viewer:** Pemantau riwayat log aktivitas perekaman di web.

---

## [v1.0.0] - 2026-08-13
### Ditambahkan
* **Rilis Perdana (MVP Core Engine):** Perekaman multi-kamera IP via stream RTSP TCP.
* **Direct Stream Copy:** Perekaman tanpa *re-encoding* CPU overhead menggunakan FFmpeg biner.
* **Segmentasi Video Otomatis:** Pemotongan per 15 menit dengan penamaan berbasis timestamp.
* **Auto-Cleanup Daemon:** Penghapusan rekaman lama berdasarkan batas hari retensi (`retention_days`).
* **Containerization:** Konfigurasi Dockerfile dan Docker Compose (`network_mode: host`).
