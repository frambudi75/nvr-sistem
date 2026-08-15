# Database & Storage Architecture - Python NVR

Sistem Python NVR dirancang dengan arsitektur penyimpanan berbasis berkas (*Flat-file / Filesystem-based Database*) untuk memaksimalkan kecepatan I/O, portabilitas, dan kemudahan backup tanpa ketergantungan pada RDBMS seperti MySQL atau PostgreSQL.

---

## 1. Struktur Hirarki Penyimpanan (`/recordings`)

Penyimpanan rekaman menggunakan struktur folder terisolasi per kamera dengan penamaan berkas berbasis waktu standar ISO.

```text
/recordings/
├── cam01/                          <-- ID Kamera unik (contoh: cam01)
│   ├── 2026-08-15_12-00-00.mp4     <-- Segmen video 15 menit
│   ├── 2026-08-15_12-15-00.mp4
│   ├── 2026-08-15_12-30-00.mp4
│   ├── ...
│   └── alerts/                     <-- Direktori snapshot AI
│       ├── alert_2026-08-15_13-45-10.jpg
│       └── alert_2026-08-15_14-12-05.jpg
│
└── cam02/
    ├── 2026-08-15_12-00-00.mp4
    └── ...
```

### Konvensi Penamaan Berkas
* **Format Berkas Video:** `YYYY-MM-DD_HH-MM-SS.mp4`
  * Contoh: `2026-08-15_13-00-00.mp4`
  * Waktu mewakili titik awal dimulainya segmen rekaman.
* **Format Berkas Alert AI:** `alert_YYYY-MM-DD_HH-MM-SS.jpg`
  * Contoh: `alert_2026-08-15_13-45-10.jpg`
  * Gambar beranotasi kotak hijau penanda subjek yang terdeteksi.

---

## 2. Skema Konfigurasi (`config.json`)

Seluruh *state* sistem, konfigurasi kamera, otentikasi, retensi, dan notifikasi disimpan dalam satu file sentral `config.json`.

```json
{
  "storage_path": "/recordings",
  "segment_time": 900,
  "retention_days": 7,
  "smart_cleanup": {
    "min_free_gb": 5
  },
  "auth": {
    "admin_user": "admin",
    "admin_pass": "admin",
    "viewer_user": "viewer",
    "viewer_pass": "viewer"
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
      "enabled": true,
      "schedule": {
        "enabled": false,
        "start_time": "08:00",
        "end_time": "18:00"
      }
    }
  ],
  "notifications": {
    "discord": {
      "enabled": true,
      "webhook_url": "https://discord.com/api/webhooks/..."
    },
    "telegram": {
      "enabled": false,
      "bot_token": "",
      "chat_id": ""
    }
  }
}
```

### Penjelasan Field:
| Field | Tipe | Deskripsi |
| :--- | :--- | :--- |
| `storage_path` | String | Path absolut direktori penyimpanan rekaman di dalam kontainer. |
| `segment_time` | Integer | Durasi per file rekaman dalam satuan detik (default: 900 / 15 menit). |
| `retention_days` | Integer | Batas umur maksimal berkas rekaman sebelum dihapus otomatis. |
| `smart_cleanup.min_free_gb` | Integer | Ambang batas sisa penyimpanan disk (GB) untuk pemicu penghapusan darurat. |
| `auth.admin_user` / `admin_pass` | String | Kredensial untuk peran Administrator (akses penuh). |
| `auth.viewer_user` / `viewer_pass` | String | Kredensial untuk peran Viewer (hanya lihat). |
| `cameras[].id` | String | Pengenal unik kamera (hanya alfanumerik & underscore). |
| `cameras[].schedule` | Object | Jadwal aktif perekaman kamera (opsional). |
| `notifications.discord` | Object | Pengaturan Webhook Discord untuk alert dan AI snapshot. |

---

## 3. Manajemen Sesi & Cache

* **Session Storage:** Menggunakan *Client-side Encrypted Cookies* bawaan Flask (`app.secret_key`).
* **Session Payload:**
  ```json
  {
    "logged_in": true,
    "username": "admin",
    "role": "admin"
  }
  ```
* **Playback Indexing:** Saat pengguna membuka tab Playback, endpoint `/api/recordings/<cam_id>` melakukan *scan* direktori lokal kamera, mem-parsing timestamp dari nama file, dan mengelompokkan berkas berdasarkan tanggal (`YYYY-MM-DD`) secara real-time tanpa memerlukan database relasional.
