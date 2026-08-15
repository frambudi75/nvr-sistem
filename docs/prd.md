# Product Requirements Document (PRD) - Python NVR System

## 1. Pendahuluan
**Nama Produk:** Python NVR (Network Video Recorder)  
**Tujuan Proyek:** Menyediakan sistem perekaman dan manajemen CCTV *self-hosted* yang mandiri, berkinerja tinggi, berbeban CPU rendah (*near-zero CPU overhead*), serta dilengkapi kapabilitas modern seperti Web Dashboard terintegrasi, kontrol hak akses berbasis peran (RBAC), dan deteksi manusia berbasis AI (*Computer Vision*).

---

## 2. Latar Belakang & Masalah yang Diselesaikan
* **Vendor Lock-in:** NVR fisik di pasaran sering kali membatasi fitur atau mengharuskan penggunaan kamera dari merek yang sama.
* **Overhead Tinggi:** Solusi NVR berbasis software yang ada (seperti Shinobi/Zoneminder) kerap kali terlalu berat untuk server mini atau hardware skala kecil/menengah.
* **Kemudahan Akses & Keamanan:** Kebutuhan sistem yang mudah dimonitor via browser modern tanpa perlu plugin tambahan, aman dari akses tidak sah, dan tidak tergantung pada layanan cloud berbayar pihak ketiga.

---

## 3. Spesifikasi & Persyaratan Teknis
* **Backend Core:** Python 3.11
* **Video Capture & Stream Processing:** FFmpeg (Binary direct copy)
* **Web Framework:** Flask + Jinja2 (Embedded REST API & Server-Sent Events)
* **Computer Vision / AI Engine:** OpenCV (`cv2.HOGDescriptor`) + NumPy
* **Notifikasi:** Discord Webhook (Multipart image upload) & Telegram Bot API
* **Containerization:** Docker & Docker Compose (`network_mode: host`)
* **Storage Hierarchy:** Local filesystem-based storage (`/recordings`)

---

## 4. Fitur Utama Sistem

### 4.1. Core Recording Engine (Direct Stream Copy)
* Menangkap stream RTSP kamera CCTV (TCP mode untuk mencegah packet loss).
* Melakukan perekaman tanpa *transcoding/re-encoding* (`-c copy`), menghemat 95%+ utilisasi CPU.
* Pemotongan segmen video otomatis (default: 15 menit / 900 detik per chunk MP4).
* Penamaan file terstruktur berbasis timestamp: `YYYY-MM-DD_HH-MM-SS.mp4`.
* Direktori terisolasi per kamera: `/recordings/{cam_id}/{filename}`.

### 4.2. Web Dashboard & Live Monitor
* **Multi-Camera Grid:** Tampilan grid interaktif status rekaman dan informasi kamera (IP, Brand, ID).
* **Live View (MJPEG Proxy):** Pemantauan streaming langsung dari RTSP ke MJPEG browser.
* **PTZ Controls:** Kontrol arah kamera (Pan/Tilt/Zoom/Stop) via ONVIF/CGI API kamera.

### 4.3. Interactive Playback & Media Tools
* **Visual Timeline Scrubber:** Penjelajah rekaman 24 jam dengan track segmen warna-warni dan *hover time indicator*.
* **Seamless Auto-Play:** Pemutaran segmen rekaman secara berkesinambungan.
* **Graceful Error Overlay:** Penanganan error codec otomatis tanpa mengunci browser (soft UI overlay).
* **Digital Zoom & Pan:** Kemampuan zoom in/out (hingga 5x) dan *drag-to-pan* langsung pada video rekaman dan live stream.
* **Video Clip Exporter:** Pemotongan klip rekaman dengan *range selector* (Start & End) dan fitur *Time-Lapse* (20x Fast Forward) langsung menjadi file MP4 unduhan.

### 4.4. AI Human Detection & Discord Alerts
* **Background Worker:** Analisis frame RTSP berkala (1 frame per 2 detik) untuk menjaga CPU tetap dingin.
* **HOG Descriptor:** Deteksi siluet manusia dengan *confidence filtering*.
* **Snapshot Annotation:** Menandai target manusia dengan kotak hijau (*bounding box*) dan menyimpan ke `/recordings/{cam_id}/alerts/`.
* **Discord Rich Alert:** Mengirimkan notifikasi instan ke webhook Discord beserta **lampiran foto bukti** deteksi.
* **Rate Limiting / Cooldown:** Anti-spam 60 detik per kamera.

### 4.5. Security & Role-Based Access Control (RBAC)
* **Session-Based Authentication:** Login terenkripsi dengan proteksi API.
* **Admin Role:** Akses penuh ke seluruh fitur, konfigurasi kamera, manajemen user, jadwal, dan penghapusan data.
* **Viewer Role:** Hak akses terbatas (hanya bisa melihat Live View dan memutar rekaman Playback), menu Settings/System/Users disembunyikan.

### 4.6. Auto-Cleanup & Smart Storage Management
* **Time-based Retention:** Penghapusan rekaman otomatis yang telah melebihi batas waktu (misal: 7 hari).
* **Smart Disk Headroom:** Pemicu penghapusan darurat jika sisa ruang disk menipis di bawah batas aman (`min_free_gb`).

### 4.7. Auto-Healing & Fault Tolerance
* Mendeteksi stream RTSP kamera yang terputus atau offline.
* Mekanisme *Auto-Reconnect* berkala secara mandiri di background.
* Fail-safe engine: jika library AI bermasalah, modul perekam dan web dashboard tetap berjalan normal.
