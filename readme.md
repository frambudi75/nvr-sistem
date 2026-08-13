# Python NVR Engine 🎥

Sebuah sistem Network Video Recorder (NVR) mandiri yang dibangun menggunakan Python dan Flask. NVR ini dirancang agar sangat ringan dengan menggunakan `FFmpeg` (`-c copy`) sehingga tidak melakukan *re-encoding* video yang memberatkan CPU. Sangat cocok untuk berjalan di Mini PC, Raspberry Pi, atau server rumah.

## ✨ Fitur Utama

- ⚡ **Sangat Ringan**: Mengandalkan *stream copy* dari RTSP langsung ke MP4.
- 🔐 **Keamanan**: Dilengkapi halaman login dan autentikasi sesi.
- 📱 **Web Dashboard**: Antarmuka web modern (Vanilla JS + CSS) yang responsif.
- 🎛️ **Live Matrix / Grid View**: Pantau semua kamera sekaligus dalam satu layar.
- ⏪ **Smart Playback**: Pemutar video terintegrasi dengan pemotongan otomatis per 15 menit.
- ⬇️ **Export Video**: Unduh video rekaman kejadian secara instan.
- 🗑️ **Auto Cleanup**: Menghapus rekaman lama secara otomatis (Bawaan: 7 hari).
- 📊 **System Monitor**: Memantau RAM, CPU, dan kapasitas Hardisk langsung dari Web.
- 🔌 **Plug & Play**: Mendukung preset berbagai kamera (Hikvision, Dahua, TP-Link Tapo, dll).

## 🚀 Cara Instalasi

Pastikan komputer/server Anda sudah terinstall **Python (3.8+)** dan **FFmpeg**.

1. Kloning repositori ini:
   ```bash
   git clone https://github.com/frambudi75/nvr-sistem.git
   cd nvr-sistem
   ```

2. Buat Virtual Environment (Opsional namun disarankan):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Untuk Linux/Mac
   venv\Scripts\activate     # Untuk Windows
   ```

3. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```

4. Jalankan sistem:
   ```bash
   python app/main.py
   ```

5. Buka Browser Anda dan akses:
   `http://localhost:5000`

> **Catatan:** Login bawaan (Default Credentials) adalah Username: `admin` dan Password: `admin`. Anda sangat disarankan untuk segera mengubahnya melalui menu **User & Security**.

## 📁 Struktur Direktori

```text
nvr-sistem/
├── app/                  # Kode inti aplikasi (Backend & Frontend)
│   ├── templates/        # File HTML (UI Web Dashboard)
│   ├── main.py           # Engine Recorder Utama
│   ├── recorder.py       # Pengendali FFmpeg
│   ├── cleanup.py        # Worker penghapus file lama otomatis
│   └── web.py            # Server Flask API
├── docs/                 # Dokumentasi arsitektur dan rancangan
├── config.json           # File konfigurasi utama (Kamera & Login)
└── nvr.log               # Catatan error dan aktivitas server
```

## 🛠️ Teknologi yang Digunakan
- **Backend:** Python, Flask, Psutil.
- **Frontend:** HTML5, CSS3, Vanilla JavaScript.
- **Video Engine:** FFmpeg (Subprocess).
