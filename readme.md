# Python NVR System 📹⚡

Sistem NVR (*Network Video Recorder*) mandiri (*self-hosted*) berkinerja tinggi berbasis **Python 3.11** dan **FFmpeg**, dilengkapi dengan antarmuka **Web Dashboard modern**, **Role-Based Access Control (RBAC)**, dan **AI Human Detection** dengan notifikasi instan ke **Discord**.

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11-brightgreen.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Direct%20Copy-007808.svg)

---

## ✨ Fitur Unggulan

* 🚀 **Near-Zero CPU Overhead (Direct Stream Copy):** Merekam video langsung tanpa *re-encoding* bitstream H.264 kamera CCTV, sangat ringan untuk server mini atau hardware hemat daya.
* 🌐 **Web Dashboard Terintegrasi (Port 5000):** Tampilan *Dark Theme Command Center* yang responsif untuk memantau status rekaman dan kamera secara real-time.
* 🕒 **24-Hour Visual Timeline Scrubber:** Penjelajah rekaman harian interaktif dengan indikator blok waktu dan pemutaran otomatis (*Auto-Play*).
* 🔍 **Digital Zoom & Pan:** Kemampuan memperbesar tampilan video (hingga 5x) dan menggeser fokus area dengan mouse drag.
* ✂️ **Video Clip Exporter:** Pemotongan klip video dengan *range selector* (Start & End) dan fitur *Time-Lapse* (20x Fast Forward) langsung menjadi file MP4 unduhan.
* 🤖 **AI Human Detection & Snapshot Alert:** Mendeteksi keberadaan manusia di background via OpenCV dan otomatis mengirim foto beranotasi kotak hijau ke Discord Webhook.
* 🛡️ **Role-Based Access Control (RBAC):** Pemisahan hak akses antara akun `Admin` (akses penuh sistem & konfigurasi) dan `Viewer` (hanya live view & playback).
* 🧹 **Auto-Cleanup & Smart Storage Retention:** Pembersihan file rekaman lama secara otomatis berdasarkan jumlah hari retensi dan penjaga ruang disk minimum (*Disk Headroom Protection*).
* 🔄 **Auto-Healing / Reconnect:** Otomatis menyambung ulang stream kamera jika koneksi jaringan sempat terputus.

---

## 🚀 Panduan Memulai Cepat (*Quick Start*)

### 1. Clone Repositori
```bash
git clone https://github.com/frambudi75/nvr-sistem.git nvr
cd nvr
```

### 2. Jalankan dengan Docker Compose
```bash
docker compose up -d --build
```

### 3. Akses Web Dashboard
Buka browser dan akses:
👉 **`http://localhost:5000`** *(atau gunakan IP Server Anda: `http://192.168.x.x:5000`)*

### 4. Kredensial Default Login
| Peran (*Role*) | Username | Password | Hak Akses |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `admin` | Akses Penuh (Tambah/Hapus Kamera, Pengaturan, User) |
| **Viewer** | `viewer` | `viewer` | Terbatas (Live View & Memutar Rekaman Playback saja) |

> [!IMPORTANT]
> Segera ubah kata sandi default di menu **User & Security** setelah Anda berhasil login pertama kali.

---

## ⚙️ Konfigurasi Kamera (`config.json`)

Kamera dapat ditambahkan langsung melalui tombol **+ Add Camera** di Web Dashboard atau diedit secara manual di `config.json`:

```json
{
  "storage_path": "/recordings",
  "segment_time": 900,
  "retention_days": 7,
  "smart_cleanup": {
    "min_free_gb": 5
  },
  "cameras": [
    {
      "id": "cam01",
      "name": "Kamera Depan",
      "brand": "hikvision",
      "ip": "10.10.0.5",
      "port": "554",
      "username": "admin",
      "password": "password_cctv",
      "rtsp_url": "rtsp://admin:password_cctv@10.10.0.5:554/Streaming/Channels/101",
      "enabled": true
    }
  ],
  "notifications": {
    "discord": {
      "enabled": true,
      "webhook_url": "https://discord.com/api/webhooks/..."
    }
  }
}
```

---

## 📂 Dokumentasi Lengkap Proyek

Dokumentasi teknis menyeluruh tersedia di dalam folder [`docs/`](./docs/):

* 📋 [PRD (Product Requirements Document)](./docs/prd.md) — Kebutuhan produk dan spesifikasi fungsional.
* 🏛️ [Arsitektur Sistem](./docs/architecture.md) — Diagram arsitektur, aliran data FFmpeg, AI worker, dan web layer.
* 💾 [Database & Storage](./docs/database.md) — Hirarki penyimpanan berkas, skema config, dan struktur timestamp.
* 🔌 [Spesifikasi REST API](./docs/api.md) — Dokumentasi endpoint API, parameter request, response, dan RBAC.
* 🎨 [Desain UI/UX](./docs/ui-ux.md) — Sistem desain dark mode, palet warna, dan interaksi komponen.
* 🚢 [Panduan Deployment & Operasional](./docs/deployment.md) — Instalasi Docker di Linux, maintenance disk, dan troubleshooting.
* 📜 [Changelog](./docs/changelog.md) — Catatan riwayat versi dan pembaruan sistem.

---

## 🛠️ Perintah Pemeliharaan Berguna

```bash
# Melihat log aktivitas NVR secara real-time
docker compose logs -f --tail 50

# Membersihkan sampah build cache Docker (menghemat puluhan GB)
docker builder prune -a -f

# Menghentikan kontainer
docker compose down
```

---

## 📄 Lisensi
Didistribusikan di bawah lisensi MIT. Silakan gunakan dan modifikasi secara bebas untuk kebutuhan pribadi maupun komersial.
