# UI/UX Design System - Python NVR Dashboard

Dokumen ini mendefinisikan panduan estetika, sistem desain, komponen antarmuka, dan alur interaksi pengguna (*user experience*) pada Python NVR Dashboard.

---

## 1. Filosofi & Estetika Desain

* **Dark Mode Native:** Menggunakan palet gelap bergaya *Cyber Security Command Center* untuk kenyamanan mata operator saat pemantauan 24/7.
* **Glassmorphism & Micro-animations:** Menggunakan efek translusen halus (`backdrop-filter: blur`), gradien modern, dan transisi halus pada status interaktif.
* **Information Hierarchy:** Informasi kritis (status rekaman, penggunaan disk, status online) selalu ditonjolkan dengan visual badges yang kontras.

---

## 2. Palet Warna & Token Desain

```css
:root {
    --bg-main: #0b0f19;         /* Latar belakang utama */
    --bg-card: #111827;         /* Latar belakang kartu/panel */
    --bg-input: #070a13;        /* Latar belakang input form */
    --border: rgba(255, 255, 255, 0.08); /* Border garis halus */
    
    --primary: #0284c7;        /* Biru aksen utama (Sky Blue) */
    --primary-hover: #0369a1;
    --success: #10b981;        /* Hijau status Online / Recording */
    --warning: #f59e0b;        /* Kuning peringatan */
    --danger: #ef4444;         /* Merah offline / error / delete */
    
    --text-main: #f9fafb;      /* Teks utama (putih terang) */
    --text-muted: #9ca3af;     /* Teks sekunder (abu-abu) */
}
```

---

## 3. Komponen Utama & Interaksi

### 3.1. Header & Navigasi Peran (RBAC)
* **Tab Navigasi:**
  * `Dashboard` (Semua Peran)
  * `System Monitor` (Khusus Admin)
  * `Settings` (Khusus Admin)
  * `User & Security` (Khusus Admin)
  * `System Logs` (Khusus Admin)
* **Status Badge:** Tombol `Logout` di pojok kanan atas dengan penanda nama pengguna aktif.

### 3.2. Live Camera Grid & Action Cards
* **Indikator Recording Berdenyut (*Pulse Animation*):**
  * Titik hijau berkedip dinamis saat kamera sedang aktif menulis data ke disk.
* **Aksi Kartu:**
  * Tombol `View` untuk membuka modal Live Stream & Playback.
  * Tombol `Edit` & `Delete` (Otomatis disembunyikan jika login sebagai *Viewer*).

### 3.3. Modal Pemutar Terpadu (Live & Playback)

#### A. Tab Live Stream & PTZ Controller
* **MJPEG Live Feed:** Menampilkan siaran langsung kamera dengan latensi rendah.
* **Digital Zoom & Pan:**
  * *Mouse Scroll Wheel:* Zoom in/out (1x hingga 5x).
  * *Click & Drag:* Menggeser area tampilan saat dalam kondisi diperbesar.
  * *Double Click:* Reset ke rasio normal (1x) atau langsung zoom 2x.
* **PTZ D-Pad Controller:** Tombol navigasi 4-arah (Atas, Bawah, Kiri, Kanan) + Tombol Stop di tengah.

#### B. Tab Playback Timeline 24 Jam
* **Date Selector Sidebar:** Menampilkan riwayat tanggal yang memiliki rekaman video.
* **Visual 24-Hour Scrubber:**
  * Garis waktu 24 jam dengan balok-balok trek biru yang merepresentasikan segmen rekaman yang ada.
  * *Hover Tooltip:* Menampilkan jam, menit, dan detik tepat di atas kursor saat diarahkan ke timeline.
  * *Click to Seek:* Mengklik timeline langsung melompat ke detik yang dipilih secara presisi.
* **Video Player & Soft Error Overlay:**
  * Otomatis memutar segmen pertama saat tanggal diklik (*Auto-Play*).
  * Menampilkan pesan kesalahan anggun (gelap transparan) di atas kotak video jika format codec video lama tidak kompatibel, tanpa memunculkan alert browser yang mengunci layar.

#### C. Video Clip Exporter Drawer
* Tombol `✂️ Export Clip` membuka panel pengunduhan klip video.
* Input Start Time & End Time dilengkapi tombol `📍 Use Current` untuk mengambil posisi waktu video yang sedang diputar.
* Checkbox `⚡ Fast-Forward Time-Lapse (20x Speed)` untuk mempercepat video berdurasi panjang menjadi ringkasan cepat.
