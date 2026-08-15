# Python NVR System 📹⚡

Sistem NVR (*Network Video Recorder*) mandiri (*self-hosted*) berkinerja tinggi berbasis **Python 3.11** dan **FFmpeg**, dilengkapi dengan antarmuka **Web Dashboard modern**, **Role-Based Access Control (RBAC)**, dan **AI Human Detection** dengan notifikasi instan ke **Discord**.

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

## 📂 Daftar Berkas Dokumentasi Teknis

Di folder `docs/` ini tersedia dokumentasi teknis mendalam:

* 📋 [PRD (Product Requirements Document)](./prd.md) — Kebutuhan produk, batasan teknis, dan spesifikasi fitur.
* 🏛️ [Arsitektur Sistem](./architecture.md) — Diagram arsitektur sistem, alur data FFmpeg, AI worker, dan web layer.
* 💾 [Database & Storage](./database.md) — Hirarki penyimpanan berkas, skema `config.json`, dan format timestamp.
* 🔌 [Spesifikasi REST API](./api.md) — Dokumentasi endpoint REST API, parameter request, response, dan RBAC.
* 🎨 [Desain UI/UX](./ui-ux.md) — Sistem desain dark mode, token warna, timeline scrubber & interaksi komponen.
* 🚢 [Panduan Deployment & Operasional](./deployment.md) — Panduan instalasi Docker di Linux, maintenance disk, dan troubleshooting.
* 📜 [Changelog](./changelog.md) — Catatan riwayat versi dan pembaruan sistem dari v1.0.0 hingga v1.4.0.
