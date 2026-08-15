# Deployment & Operations Guide - Python NVR

Panduan lengkap untuk melakukan instalasi, konfigurasi, dan pemeliharaan server Python NVR di lingkungan produksi berbasis Linux / Docker.

---

## 1. Prasyarat Sistem (*Prerequisites*)

* **Sistem Operasi:** Linux (Ubuntu 20.04/22.04/24.04, Debian 11/12, atau Rocky Linux)
* **Docker & Docker Compose:** Versi terbaru (Docker Engine 24.x+, Compose v2)
* **Hardware Minimum:**
  * CPU: 2 Core (Intel/AMD/ARM)
  * RAM: 2 GB (Disarankan 4 GB untuk pemrosesan AI Multi-Kamera)
  * Disk: SSD/HDD kapasitas sesuai kebutuhan retensi rekaman
* **Jaringan:** IP Statis pada server dan kamera CCTV, port 5000 (Web UI) dan port 554 (RTSP).

---

## 2. Struktur Berkas Proyek

```text
nvr/
├── app/
│   ├── templates/
│   │   └── index.html
│   ├── ai_detector.py
│   ├── cleanup.py
│   ├── main.py
│   ├── notifier.py
│   ├── recorder.py
│   └── web.py
├── docs/
├── recordings/          <-- Direktori rekaman lokal host
├── config.json          <-- Konfigurasi utama
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 3. Konfigurasi Docker Compose

`docker-compose.yml`:
```yaml
services:
  nvr-core:
    build: .
    container_name: python-nvr
    restart: unless-stopped
    network_mode: "host"
    volumes:
      - ./recordings:/recordings
      - ./config.json:/config.json
    environment:
      - TZ=Asia/Jakarta
```

> [!NOTE]
> **Mengapa menggunakan `network_mode: "host"`?**  
> `network_mode: "host"` memberikan akses jaringan langsung ke subnet kamera lokal tanpa overhead NAT Docker, mempermudah penemuan IP kamera lokal (10.x.x.x / 192.168.x.x), dan mengoptimalkan performa transfer streaming RTSP volume tinggi.

---

## 4. Langkah Instalasi & Menjalankan

### Langkah 1: Clone Repositori
```bash
git clone https://github.com/frambudi75/nvr-sistem.git nvr
cd nvr
```

### Langkah 2: Siapkan Direktori Penyimpanan
```bash
mkdir -p recordings
chmod -R 777 recordings
```

### Langkah 3: Build & Jalankan Kontainer
```bash
docker compose build --no-cache
docker compose up -d
```

### Langkah 4: Akses Dashboard
Buka browser dan kunjungi:
👉 **`http://<IP_SERVER_ANDA>:5000`**

* **Default Admin Login:** Username: `admin` | Password: `admin`
* **Default Viewer Login:** Username: `viewer` | Password: `viewer`

*(Segera ubah kredensial default ini di menu **User & Security** setelah login pertama kali).*

---

## 5. Pemeliharaan & Operasional (*Maintenance*)

### 5.1. Melihat Log Kontainer
```bash
# Log NVR secara real-time
docker compose logs -f --tail 50
```

### 5.2. Memeriksa Penggunaan Disk & Cache
```bash
# Cek ruang disk server
df -h

# Cek penggunaan ruang oleh Docker
docker system df

# Membersihkan sampah build cache Docker (mereclaim belasan GB)
docker builder prune -a -f
```

### 5.3. Restart / Reload Konfigurasi
Jika Anda mengubah file `config.json` secara manual di server:
```bash
docker compose restart
```

---

## 6. Panduan Troubleshooting

| Gejala Masalah | Penyebab Umum | Solusi |
| :--- | :--- | :--- |
| **`MEDIA_ERR_SRC_NOT_SUPPORTED`** saat memutar video | Kamera menggunakan codec `H.264+` atau `H.265` yang tidak didukung browser | Matikan fitur *Smart Codec / H.264+ / H.265+* di pengaturan web IP Camera Anda. Gunakan **Standard H.264**. |
| **Container `Restarting` berulang kali** | Konflik dependensi Python atau library OS yang hilang | Jalankan `docker compose build --no-cache` untuk memperbarui image dengan versi dependensi yang sudah dipin (`opencv-python-headless==4.9.0.80`, `numpy<2`). |
| **`ERR_CONNECTION_REFUSED` pada port 5000** | Web server Flask belum aktif atau port terhalang firewall | Pastikan container berstatus *Running*, coba akses via `http://` (tanpa s), dan buka port: `sudo ufw allow 5000`. |
| **Notifikasi Discord tidak terkirim** | URL Webhook salah atau server tidak memiliki akses internet outbound | Periksa koneksi internet server dan uji webhook di tab *Settings* -> *Test Notification*. |
