# REST API Specification - Python NVR

Seluruh endpoint API disajikan oleh web server Flask pada port `5000`.

---

## 1. Konsep Dasar & Otentikasi

* **Content-Type:** `application/json` (kecuali streaming dan ekspor file).
* **Proteksi Sesi:** Pengguna wajib login terlebih dahulu via `/login` untuk mendapatkan cookie sesi.
* **Format Error Standar:**
  ```json
  {
    "status": "error",
    "message": "Pesan deskripsi kesalahan"
  }
  ```

---

## 2. Daftar Endpoint

### 2.1. Otentikasi

#### `POST /login`
Melakukan otentikasi pengguna dan menginisialisasi sesi.
* **Akses:** Publik
* **Content-Type:** `application/x-www-form-urlencoded`
* **Body:**
  * `username` (string): Nama pengguna
  * `password` (string): Kata sandi
* **Response:** Redirect ke dashboard `/` jika sukses, atau kembali ke `/login` jika gagal.

#### `GET /logout`
Mengakhiri sesi dan menghapus cookie otentikasi.
* **Akses:** `@login_required`

---

### 2.2. Kamera & Konfigurasi

#### `GET /api/cameras`
Mengambil daftar status kamera secara real-time.
* **Akses:** `@login_required` (Admin & Viewer)
* **Response (200 OK):**
  ```json
  [
    {
      "id": "cam01",
      "name": "Kamera Depan",
      "brand": "hikvision",
      "ip": "10.10.0.5",
      "status": "online",
      "recording": true
    }
  ]
  ```

#### `GET /api/config`
Mengambil seluruh isi konfigurasi sistem.
* **Akses:** `@admin_required` (Hanya Admin)
* **Response (200 OK):** Objek JSON `config.json`.

#### `POST /api/config`
Menyimpan dan mengaplikasikan perubahan konfigurasi sistem.
* **Akses:** `@admin_required`
* **Body:** Objek JSON `config.json` lengkap.
* **Response (200 OK):**
  ```json
  {
    "status": "success",
    "message": "Configuration updated successfully."
  }
  ```

---

### 2.3. Perekaman & Media Playback

#### `GET /api/recordings/<cam_id>`
Mengambil daftar rekaman video yang tersedia untuk kamera tertentu, dikelompokkan berdasarkan tanggal.
* **Akses:** `@login_required` (Admin & Viewer)
* **Response (200 OK):**
  ```json
  [
    {
      "date": "2026-08-15",
      "files": [
        {
          "name": "2026-08-15_12-00-00.mp4",
          "path": "/recordings/cam01/2026-08-15_12-00-00.mp4",
          "size": "45.2 MB",
          "time": "12:00:00"
        }
      ]
    }
  ]
  ```

#### `POST /api/recordings/export_clip`
Memotong segmen rekaman video tertentu dari timeline dan mengunduhnya sebagai berkas MP4 tunggal.
* **Akses:** `@login_required` (Admin & Viewer)
* **Body:**
  ```json
  {
    "cam_id": "cam01",
    "date": "2026-08-15",
    "start_time": "14:15:00",
    "end_time": "14:20:00",
    "time_lapse": false
  }
  ```
* **Response (200 OK):** Binary file stream (`video/mp4`) sebagai file unduhan.

#### `POST /api/storage/cleanup/run_auto`
Memicu eksekusi aturan pembersihan otomatis (retensi hari & ruang disk minimum) secara instan.
* **Akses:** `@admin_required`
* **Response (200 OK):**
  ```json
  {
    "status": "success",
    "message": "Auto-cleanup triggered successfully."
  }
  ```

#### `POST /api/storage/cleanup/manual`
Melakukan pembersihan manual berdasarkan umur file, kamera tertentu, atau pembersihan snapshot AI alerts.
* **Akses:** `@admin_required`
* **Body:**
  ```json
  {
    "days": 3,
    "cam_id": "all",
    "clear_alerts": false
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "status": "success",
    "deleted_files": 24,
    "freed_mb": 1150.5,
    "message": "Successfully deleted 24 files, freeing 1150.5 MB."
  }
  ```

#### `DELETE /api/recordings/<cam_id>/date/<date_str>`
Menghapus seluruh rekaman untuk kamera tertentu pada tanggal tertentu (`YYYY-MM-DD`).
* **Akses:** `@admin_required`
* **Response (200 OK):**
  ```json
  {
    "status": "success",
    "deleted_files": 96,
    "freed_mb": 4200.0,
    "message": "Deleted 96 files for date 2026-08-21 (4200.0 MB freed)."
  }
  ```

---

### 2.4. Live Streaming & PTZ

#### `GET /live_stream/<cam_id>`
Menyajikan stream langsung kamera dalam format MJPEG via HTTP multipart stream.
* **Akses:** `@login_required` (Admin & Viewer)
* **Response Headers:** `Content-Type: multipart/x-mixed-replace; boundary=frame`

#### `POST /api/ptz`
Mengirimkan perintah pergerakan kamera (Pan / Tilt / Zoom / Stop).
* **Akses:** `@admin_required`
* **Body:**
  ```json
  {
    "cam_id": "cam01",
    "action": "up"
  }
  ```
* **Pilihan Action:** `up`, `down`, `left`, `right`, `zoom_in`, `zoom_out`, `stop`.

---

### 2.5. Monitoring & Notifikasi

#### `GET /api/system/stats`
Mengambil metrik performa server (CPU, Memori, Disk).
* **Akses:** `@login_required` (Admin & Viewer)
* **Response (200 OK):**
  ```json
  {
    "cpu_usage": 3.5,
    "memory": {
      "total": 3.77,
      "used": 0.85,
      "percent": 22.5
    },
    "disk": {
      "total": 49.0,
      "used": 9.7,
      "free": 37.3,
      "percent": 21.0
    }
  }
  ```

#### `GET /api/logs`
Mengambil baris log sistem NVR terbaru.
* **Akses:** `@admin_required`
* **Query Params:** `lines` (opsional, default 100)
* **Response (200 OK):**
  ```json
  {
    "logs": "2026-08-15 16:00:00 - NVR-Main - INFO - Syncing cameras..."
  }
  ```

#### `POST /api/notifications/test`
Menguji pengiriman notifikasi test ke Discord atau Telegram.
* **Akses:** `@admin_required`
* **Body:**
  ```json
  {
    "type": "discord"
  }
  ```
