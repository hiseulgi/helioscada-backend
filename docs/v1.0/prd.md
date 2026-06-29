# Product Requirements Document (PRD)
# HELIOSCADA — Aplikasi Mobile Monitoring Modul Praktikum Energi Surya

- **Versi:** 1.0 (MVP)
- **Tanggal:** 11 Juni 2026
- **Target Pengguna:** Mahasiswa program studi sistem pembangkit energi (non-IT background)

---

## 1. Pernyataan Masalah

Modul praktikum panel surya di laboratorium SCADA PENS tidak memiliki antarmuka visual yang memadai, sehingga mahasiswa hanya dapat membaca data parameter kelistrikan dari tampilan multimeter atau layar LCD 20×4 yang terbatas, tanpa kemampuan melihat aliran energi secara holistik, menganalisis data historis, maupun mengontrol beban secara terintegrasi dari satu perangkat.

---

## 2. Solusi

**Proposisi Nilai:**
HELIOSCADA adalah aplikasi mobile berbasis Flutter yang terhubung ke modul kit panel surya via MQTT di jaringan lokal lab, memberikan visualisasi aliran energi real-time, analisis data historis, dan kontrol beban AC langsung dari smartphone mahasiswa.

**Mengapa Lebih Baik dari Cara Saat Ini?**

| Kondisi Saat Ini | Dengan HELIOSCADA |
|---|---|
| Baca data satu per satu dari LCD 20×4 dan multimeter | Semua parameter tampil sekaligus dalam satu layar dengan visual flow diagram |
| Tidak ada riwayat data — mahasiswa harus mencatat manual | Data log tersimpan di database, bisa difilter dan diekspor ke `.CSV` untuk laporan |
| Tidak bisa mengontrol beban dari jarak jauh | Toggle relay kipas/lampu dari smartphone via MQTT |
| Estimasi SoC baterai tidak tersedia | Nilai SoC ditampilkan sebagai gauge + grafik tren Dual-Axis |

---

## 3. Fitur MVP (Maksimal 5)

1. **Real-Time Energy Flow Dashboard**
   Tampilan diagram aliran daya `PV → Baterai → Inverter → Beban` dengan data sensor live (tegangan, arus, daya, suhu) dan gauge estimasi SoC baterai.

2. **Relay Load Control (dengan Konfirmasi)**
   Dua toggle switch untuk menghidupkan/mematikan Kipas AC dan Lampu Pijar via perintah MQTT. Setiap aksi memicu pop-up konfirmasi keselamatan sebelum dieksekusi.

3. **Analytics & Log Data (Double Selector)**
   Grafik data historis yang dapat difilter berdasarkan rentang waktu (Datetime Picker) dan komponen (Tab: PV / Baterai / Inverter), dengan pilihan parameter grafik via Choice Chips.

4. **Ekspor Data Log ke `.CSV`**
   Tombol unduh di halaman Analytics untuk mengekspor data hasil filter ke file `.CSV` agar mahasiswa dapat mengolahnya di laptop untuk laporan resmi.

5. **Konfigurasi Koneksi Jaringan Lokal**
   Form input alamat IP broker MQTT dan port, dilengkapi tombol *Test Connection* untuk memverifikasi koneksi sebelum sesi praktikum dimulai.

---

## 4. Alur Pengguna (User Flow)

Alur lengkap dari mahasiswa masuk lab hingga menyelesaikan sesi praktikum:

```
[1] Buka Aplikasi
        │
        ▼
[2] Halaman Settings (Pertama Kali / Belum Terhubung)
    → Mahasiswa memasukkan IP Broker MQTT dan Port
    → Tekan [ Test Connection ]
    → Indikator berubah Hijau = Terhubung ✓
        │
        ▼
[3] Navigasi ke Halaman Dashboard (Home)
    → Lihat diagram aliran energi PV → Baterai → Inverter → Beban
    → Pantau data real-time: Vpv, Ipv, Ppv, Tpv, Vbat, Ibat, Pbat, Tbat, SoC (%), Vload, Iload, Pload, Efisiensi inverter (%)
    → Warna Ibat: Hijau (+) = Sedang Diisi | Merah (-) = Sedang Dikosongkan
        │
        ▼
[4] Kontrol Beban (Masih di Halaman Dashboard)
    → Tekan Toggle "Kipas AC" atau "Lampu Pijar"
    → Muncul Pop-up Konfirmasi: "Yakin ingin menyalakan Kipas AC?"
    → Tekan [ Konfirmasi ] → Perintah dikirim via MQTT → Relay aktif
        │
        ▼
[5] Navigasi ke Halaman Analytics
    → Pilih rentang waktu sesi dengan [ 📅 Datetime Picker ]
    → Pilih komponen di Tab Tingkat 1: [ PV Panel ] | [ Baterai ] | [ Inverter ]
    → Pilih parameter di Chip Tingkat 2 (misal: [ Daya PV ], [ Tren SoC vs V ])
    → Grafik muncul otomatis sesuai pilihan
        │
        ▼
[6] Ekspor Data untuk Laporan
    → Tekan tombol [ ⬇️ Ekspor Log ke .CSV ] di bagian bawah Analytics
    → File .CSV tersimpan di storage HP
    → Mahasiswa upload/transfer file ke laptop untuk diolah di Excel
        │
        ▼
[7] Selesai Sesi Praktikum ✓
```

---

## 5. Batasan & Langkah Selanjutnya

### Apa yang TIDAK Termasuk dalam MVP:

- ❌ Autentikasi / Login pengguna (tidak ada sistem akun)
- ❌ Notifikasi push / alarm berbasis push notification system
- ❌ Kalibrasi offset sensor dari dalam aplikasi (Settings hanya untuk konfigurasi jaringan di MVP)
- ❌ Ekspor format selain `.CSV` (misal: PDF laporan otomatis)
- ❌ Multi-kit / multi-node (hanya satu kit PV yang dipantau)
- ❌ Grafik Korelasi Suhu vs Daya (X-Y Scatter Plot) — ditunda ke v1.1
- ❌ Halaman "Informasi Hardware Kit" (specs komponen fisik) — ditunda ke v1.1

### Apa yang Dapat Ditambahkan Nanti (Post-MVP):

- ✅ **v1.1:** Kalibrasi offset sensor dari Settings, grafik korelasi suhu vs daya, halaman spesifikasi hardware
- ✅ **v1.2:** Alert banner notifikasi lokal (SoC < 20%, suhu kritis) menggunakan local notifications Flutter
- ✅ **v2.0:** Multi-kit support, halaman perbandingan dua sesi praktikum, auto-generate template laporan PDF
- ✅ **v2.0:** Panduan interaktif langkah demi langkah (in-app tutorial modul praktikum)

---

## 6. Tech Stack

### Mobile App (Flutter)

| Layer | Library / Tool | Fungsi |
|---|---|---|
| **Framework** | Flutter (Dart) | UI cross-platform Android |
| **Architecture** | Clean Architecture | Struktur kode yang terorganisir |
| **State Management** | Riverpod | Manajemen state data real-time sensor |
| **Routing** | GoRouter | Navigasi antar halaman (Dashboard, Analytics, Settings) |
| **MQTT Client** | `mqtt_client` | Subscribe/Publish ke Mosquitto broker |
| **HTTP Client** | `dio` | HTTP REST untuk fetch data log dari backend |
| **Charting** | `syncfusion_flutter_charts` | Grafik time-series dan dual-axis |
| **Storage** | `shared_preferences` | Simpan konfigurasi IP MQTT lokal |
| **CSV Export** | `csv` + `path_provider` | Generate dan simpan file `.CSV` |

### Komunikasi Data

| Layer | Teknologi | Fungsi |
|---|---|---|
| **Real-time** | **MQTT (Mosquitto)** | Subscribe topik `laboratorium/scada/pv_kit` untuk data sensor live (interval 1 detik) |
| **Historis** | **HTTP REST** | Fetch data log dari backend untuk ditampilkan di grafik Analytics |
| **Kontrol** | **MQTT Publish** | Kirim perintah relay ke ESP32 via topik MQTT |

### Backend Server (PC Lab)

| Layer | Teknologi | Fungsi |
|---|---|---|
| **API** | FastAPI (Python) | Endpoint REST untuk query data historis dari database |
| **Database** | PostgreSQL | Penyimpanan data log sensor dengan timestamp |
| **Validasi Data** | Pydantic | Schema validasi JSON payload dari ESP32 |
| **MQTT Broker** | Mosquitto | Message broker lokal untuk komunikasi ESP32 ↔ App |

### Firmware (ESP32)

| Layer | Teknologi | Fungsi |
|---|---|---|
| **RTOS** | FreeRTOS | Dual-core: Core 1 sampling sensor, Core 0 publish MQTT |
| **Protocol** | MQTT (JSON Payload) | Publish data sensor tiap 1 detik ke broker |
| **Koneksi** | Wi-Fi (Jaringan Lokal Lab) | Terhubung ke Access Point lab PENS |

### Payload JSON (Contoh Struktur Data dari ESP32)

```json
{
  "timestamp": "2026-06-11T10:30:00",
  "pv": { "v": 18.4, "i": 2.1, "p": 38.6, "t": 52.3 },
  "battery": { "v": 12.6, "i": 1.8, "p": 22.7, "soc": 78.5, "t": 31.2 },
  "inverter": { "v_ac": 220.1, "i_ac": 0.12, "p_ac": 26.4, "eff": 95.2 },
  "relay": { "fan": false, "lamp": true }
}
```

---

> **Catatan Penting untuk AI Coding:**
> MVP ini dirancang agar dapat dibangun secara linear:
> 1. Mulai dari **Settings** (koneksi MQTT, tidak butuh backend)
> 2. Lanjut **Dashboard** (subscribe MQTT, tampilkan data, toggle relay)
> 3. Terakhir **Analytics** (butuh backend FastAPI + PostgreSQL)
>
> Scope ini dapat dikerjakan dengan *vibe coding* menggunakan Cursor/Copilot dalam 2–4 minggu oleh satu developer.
