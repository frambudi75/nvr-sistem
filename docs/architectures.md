# Arsitektur Sistem NVR

Dokumen ini menjelaskan rancangan teknis (*technical design*) dari sistem Python NVR.

## Konsep Tingkat Tinggi (*High-Level Concept*)
Sistem NVR dipecah menjadi desain *headless* (tanpa UI). Perekam bekerja secara asinkron di belakang layar mengurus *stream* video, sementara pengelolaan file dilakukan dalam *thread* terpisah. Sistem ini dibungkus secara menyeluruh oleh Docker untuk standardisasi *environment*.

## Komponen Sistem

### 1. NVR Core Engine (Python)
*   `app/main.py`: Bertindak sebagai orkestrator utama (*entry point*). Ia membaca `config.json`, lalu melakukan *spawn* (memunculkan) *instance* `Recorder` untuk setiap kamera yang statusnya `enabled: true`.
*   `app/recorder.py`: Kelas yang membungkus modul `subprocess`. 
    *   **Mekanisme:** Ia mengeksekusi perintah biner FFmpeg.
    *   **Efisiensi:** Menggunakan flag `-c copy` pada FFmpeg. Artinya, *stream* dari kamera CCTV (biasanya sudah berbentuk H.264 atau H.265) langsung disalin bit-demi-bit ke dalam file MP4 di *hard drive*. Proses ini membutuhkan **0% beban CPU untuk *encoding***, menjadikannya sangat ringan meski dipasang belasan kamera.
    *   **Segmentasi:** Menggunakan `-f segment` untuk secara *native* menyuruh FFmpeg memotong file saat mencapai durasi tertentu (misal: per 15 menit), tanpa menjatuhkan/menghentikan *stream*.
*   `app/cleanup.py`: Dijalankan di dalam *thread* daemon yang bangun setiap 1 jam sekali. Ia melakukan *traversing* (penjelusuran direktori) ke dalam *storage_path* dan menghapus video yang atribut waktu modifikasinya (*mtime*) lebih tua dari `retention_days`.

### 2. Konfigurasi
*   Semua *state* (kamera, direktori) disuntikkan secara dinamis melalui `config.json`.
*   Pendekatan ini memisahkan konfigurasi dari kode (memenuhi prinsip *12-factor app*), sehingga penambahan kamera baru tidak memerlukan proses *re-build* aplikasi.

### 3. Docker & Deployment
*   **Base Image:** `python:3.11-slim` digunakan untuk meminimalisir ukuran *image*.
*   **Dependency:** Paket biner `ffmpeg` diinstal di tingkat OS Debian (di dalam Dockerfile) karena `subprocess` membutuhkannya untuk dieksekusi secara global.
*   **Volume Mounts:** Direktori `./recordings` di-*mount* ke dalam kontainer. Ini bersifat krusial agar NVR (kontainer) menulis data langsung ke disk *host*, memastikan video tidak hilang saat kontainer mati.

## Rencana Integrasi Frontend (Masa Depan)
Karena *storage* diletakkan dalam sistem *file* biasa di *host* (`./recordings`), mengintegrasikan antarmuka Web (Frontend) sangat mudah:
1. Aplikasi web (seperti PHP Native) bisa cukup diletakkan di direktori sejajar.
2. PHP dapat diinstruksikan untuk memindai isi direktori `./recordings`.
3. File `.mp4` disajikan menggunakan tag `<video>` standar HTML5 karena format `.mp4` dengan *codec* bawaan kamera rata-rata sudah *web-compatible*.
