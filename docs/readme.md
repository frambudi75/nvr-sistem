# Python NVR (Network Video Recorder)

Sistem NVR mandiri, ringan, dan stabil yang dibangun menggunakan Python dan Docker. Sistem ini dirancang untuk merekam aliran video RTSP dari kamera IP secara terus-menerus tanpa membebani server (*stream copy* via FFmpeg).

## Fitur Utama
*   **Perekaman Ringan:** Menggunakan FFmpeg `-c copy` untuk menyimpan *stream* video RTSP secara langsung tanpa *encoding* ulang.
*   **Segmentasi Otomatis:** Video akan dipotong secara otomatis pada interval tertentu (contoh: per 15 menit) untuk memudahkan pencarian dan mencegah korupsi file berukuran raksasa.
*   **Auto-Retention (Pembersihan Otomatis):** Skrip pembersih (*cleanup*) berjalan di *background* untuk menghapus video lama (contoh: lebih dari 7 hari) sehingga kapasitas *hard drive* selalu terjaga.
*   **Konfigurasi Fleksibel:** Daftar kamera IP dan pengaturan NVR dapat diubah dengan mudah melalui file `config.json`.
*   **Dockerized:** Sangat mudah di-_deploy_, di-*restart*, dan di-*maintain* berkat kontainerisasi Docker.

## Prasyarat
Sistem NVR ini wajib berjalan di atas Docker. Anda harus memiliki:
1. Docker Engine / Docker Desktop
2. Docker Compose (sudah sepaket dalam Docker Desktop)

## Panduan Instalasi dan Penggunaan

1. **Persiapan Konfigurasi**
   Buka file `config.json` di *root* proyek. Sesuaikan URL RTSP dan nama kamera sesuai dengan yang Anda miliki.
   ```json
   {
     "storage_path": "/recordings",
     "retention_days": 7,
     "segment_time": 900,
     "cameras": [
       {
         "id": "kamera_garasi",
         "name": "Garasi Depan",
         "rtsp_url": "rtsp://admin:password123@192.168.1.50:554/stream1",
         "enabled": true
       }
     ]
   }
   ```
   *Catatan:* `segment_time` diatur dalam hitungan detik. `900` = 15 Menit.

2. **Menjalankan Sistem NVR**
   Buka terminal/Command Prompt di folder proyek ini (`nvr/`), lalu jalankan perintah:
   ```bash
   docker-compose up -d --build
   ```

3. **Melihat Hasil Rekaman**
   Video akan mulai direkam dan disimpan di folder `recordings/` (yang dibuat secara otomatis di direktori utama). Folder ini di-_mount_ ke dalam *container* Docker sehingga file fisiknya tetap aman di komputer *host*. File disimpan dalam format `.mp4`.

4. **Melihat Log (Troubleshooting)**
   Jika ada kamera yang gagal merekam, Anda bisa melihat log sistem dengan:
   ```bash
   docker-compose logs -f
   ```

5. **Menghentikan Sistem**
   Untuk mematikan sistem NVR:
   ```bash
   docker-compose down
   ```

## Langkah Selanjutnya
*   **Web Dashboard:** Proyek ini saat ini bertindak murni sebagai "Mesin Perekam" (Backend). Langkah selanjutnya adalah mengembangkan Web Dashboard (misal: dengan PHP Native atau Flask) yang dapat menampilkan file-file di folder `recordings` ke dalam antarmuka web yang ramah pengguna.
