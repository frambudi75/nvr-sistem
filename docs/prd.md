# Product Requirements Document (PRD) - Python NVR

## 1. Pendahuluan
**Tujuan Proyek:** Membangun Sistem NVR (*Network Video Recorder*) mandiri yang *self-hosted* untuk keperluan keamanan, yang mampu merekam dari IP Camera dengan stabil dan efisien.

## 2. Masalah yang Diselesaikan
*   Solusi NVR di pasaran (NVR fisik) kurang fleksibel, sering terkunci pada merek tertentu (Vendor Lock-in).
*   Solusi NVR *software* yang ada kadang terlalu kompleks atau berat untuk spesifikasi server menengah ke bawah.
*   Perlunya sistem yang mudah dikonfigurasi dan dipindahkan (*portable*) antar server.

## 3. Spesifikasi & Persyaratan Teknis
*   **Teknologi Utama Backend:** Python 3
*   **Pemrosesan Video:** FFmpeg
*   **Containerization:** Docker & Docker Compose
*   **Keterbatasan (Constraints):**
    *   TIDAK MENGGUNAKAN Node.js (untuk menghindari kekhawatiran penggunaan memori/*overhead* ekosistem V8 pada proses *background* berkelanjutan).
    *   CPU Load harus sekecil mungkin.

## 4. Fitur-Fitur Utama (MVP - Minimum Viable Product)

### 4.1. Fitur Perekaman (*Recording Engine*)
*   Menarik *stream* RTSP (TCP) dari kamera.
*   Melakukan perekaman video ke dalam direktori lokal server.
*   Perekaman dilakukan tanpa mengubah kualitas atau struktur video asli (*Direct Stream Copy*).
*   Mendukung penambahan sistem multikamera (skalabilitas horizontal).

### 4.2. File Management & Segmentasi
*   Video tidak boleh berupa satu *file* utuh berdurasi 24 jam.
*   Sistem otomatis melakukan pemotongan rekaman per `N` menit (opsi konfigurasi, contoh: 15 menit).
*   Penamaan *file* harus jelas berbasis stempel waktu (*Timestamp*), contoh: `YYYY-MM-DD_HH-MM-SS.mp4`.
*   Setiap kamera harus memiliki sub-direktorinya masing-masing (`/recordings/nama_kamera/`).

### 4.3. Auto-Cleanup / Data Retention
*   Sistem mampu menghapus file rekaman lawas secara berkala.
*   Terdapat batas umur maksimal file (contoh: 7 hari).
*   Bertujuan untuk menjaga agar kapasitas penyimpanan (*Hard Disk / SSD*) tidak tembus 100%.

### 4.4. Toleransi Kegagalan (Fault Tolerance)
*   Sistem harus mendeteksi jika koneksi ke kamera terputus atau proses FFmpeg mati (karena gangguan jaringan).
*   Sistem harus mencoba menyambung ulang (*auto-reconnect*) aliran RTSP yang terputus secara otomatis tanpa intervensi pengguna.

## 5. Ruang Lingkup Luar (Out-of-Scope untuk Saat Ini)
Hal-hal berikut belum diimplementasikan di versi pertama (MVP), namun direncanakan sebagai pengembangan lanjutan:
*   **Web Dashboard UI:** (Bisa diimplementasikan terpisah dengan PHP/lainnya).
*   **Motion Detection (AI):** Mendeteksi pergerakan manusia/objek.
*   **Real-time Alerts:** Notifikasi ke Telegram/Email jika ada gerakan.
