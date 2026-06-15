# System Specification — HELIOSCADA
### Spesifikasi Database, API Contracts, dan MQTT Protocol

**Versi:** 1.0 (MVP)  
**Terakhir Diperbarui:** 11 Juni 2026  
**Backend Tech:** FastAPI, PostgreSQL, Pydantic, Mosquitto MQTT, Docker  

---

## 1. Database Design (PostgreSQL)

Untuk data IoT deret waktu (time-series) berskala laboratorium, skema database dirancang sederhana namun optimal. Penggunaan indeks pada kolom `timestamp` krusial untuk mempercepat pencarian data saat mahasiswa memfilter tanggal grafik.

### A. Tabel Utama: `telemetry_logs`
Tabel ini menyimpan semua parameter pengukuran dari sensor DC, sensor AC, sensor suhu, estimasi SoC baterai, serta status relay aktif pada setiap detik pengiriman data.

```sql
CREATE TABLE telemetry_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Parameter Solar Panel (PV)
    pv_voltage NUMERIC(5, 2) NOT NULL,       -- Volt (V), contoh: 18.42
    pv_current NUMERIC(5, 2) NOT NULL,       -- Ampere (A), contoh: 2.15
    pv_power NUMERIC(6, 2) NOT NULL,         -- Watt (W), contoh: 39.60
    pv_temperature NUMERIC(4, 1) NOT NULL,   -- Derajat Celcius (°C), contoh: 52.3
    
    -- Parameter Baterai & SoC
    battery_voltage NUMERIC(5, 2) NOT NULL,   -- Volt (V), contoh: 12.60
    battery_current NUMERIC(5, 2) NOT NULL,   -- Ampere (A), nilai (+) charging, (-) discharging
    battery_power NUMERIC(6, 2) NOT NULL,     -- Watt (W), contoh: 22.68
    battery_soc NUMERIC(5, 2) NOT NULL,       -- Persentase (%), contoh: 78.50
    battery_soc_status VARCHAR(50) NOT NULL,  -- Status algoritma SoC: 'Coulomb Counting' atau 'Calibrated via Lookup Table'
    battery_temperature NUMERIC(4, 1) NOT NULL, -- Derajat Celcius (°C) suhu ambient, contoh: 31.2
    
    -- Parameter Inverter (AC)
    inverter_voltage_ac NUMERIC(5, 2) NOT NULL, -- Volt AC (V), contoh: 220.10
    inverter_current_ac NUMERIC(5, 2) NOT NULL, -- Ampere AC (A), contoh: 0.12
    inverter_power_ac NUMERIC(6, 2) NOT NULL,   -- Watt AC (W), contoh: 26.40
    inverter_efficiency NUMERIC(5, 2) NOT NULL, -- Persentase (%), contoh: 95.20
    
    -- Status Relay (Aktuator)
    relay_fan BOOLEAN NOT NULL DEFAULT FALSE,   -- TRUE = ON, FALSE = OFF
    relay_lamp BOOLEAN NOT NULL DEFAULT FALSE   -- TRUE = ON, FALSE = OFF
);

-- Indeks untuk optimasi query berdasarkan range waktu (grafik & export CSV)
CREATE INDEX idx_telemetry_timestamp ON telemetry_logs (timestamp DESC);
```

### B. Tabel Log Aksi Kontrol: `control_logs` (Opsional untuk Audit Praktikum)
Tabel ini mencatat riwayat kapan relay dinyalakan atau dimatikan oleh mahasiswa untuk keperluan evaluasi praktikum.

```sql
CREATE TABLE control_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    device VARCHAR(20) NOT NULL,  -- 'fan' atau 'lamp'
    action VARCHAR(10) NOT NULL,  -- 'ON' atau 'OFF'
    status VARCHAR(20) NOT NULL   -- 'SUCCESS' atau 'FAILED'
);
```

---

## 2. API Specification (FastAPI REST Contracts)

API Backend digunakan oleh Aplikasi Mobile untuk memuat data riwayat (analitik) dan mengekspor CSV. Format data yang dikirim dan diterima menggunakan JSON.

### Base URL
`http://<server-ip>:8000`

---

### A. Health Check Jaringan
Mengecek apakah server backend aktif dan terhubung ke database.

*   **Endpoint:** `GET /health`
*   **Request Headers:** None
*   **Response (200 OK):**
    ```json
    {
      "status": "healthy",
      "database": "connected",
      "timestamp": "2026-06-11T15:05:00Z"
    }
    ```

---

### B. Ambil Riwayat Telemetri (Data Grafis)
Mengambil data historis berdasarkan rentang waktu dan komponen tertentu. Untuk menghemat bandwidth jaringan lokal lab dan mengurangi beban memori di HP, backend secara dinamis menyaring field yang dikirim berdasarkan parameter `component`. Jika `component` diset selain `all`, server hanya mengirimkan `timestamp` dan sub-objek komponen terpilih.

Selain itu, backend menerapkan kompresi data (*downsampling*) otomatis menggunakan algoritma pembagi waktu rata-rata (atau *LTTB - Largest Triangle Three Buckets*) jika jumlah baris di DB melebihi `downsample_limit`.

*   **Endpoint:** `GET /api/v1/telemetry`
*   **Query Parameters:**
    *   `start_time` (string, ISO 8601): Awal rentang waktu, wajib. Contoh: `2026-06-11T08:00:00Z`
    *   `end_time` (string, ISO 8601): Akhir rentang waktu, wajib. Contoh: `2026-06-11T11:00:00Z`
    *   `component` (string): Pilihan komponen. Pilihan: `pv`, `battery`, `inverter`, `all` (default: `all`)
    *   `downsample_limit` (integer): Mengompresi jumlah titik data yang dikirim ke HP agar grafik tidak lag (default: `500`)

*   **Response (200 OK) - Jika `component=all`:**
    ```json
    {
      "count": 2,
      "data": [
        {
          "timestamp": "2026-06-11T08:00:00Z",
          "pv": { "v": 18.4, "i": 2.1, "p": 38.6, "t": 52.3 },
          "battery": { "v": 12.6, "i": 1.8, "p": 22.7, "soc": 78.5, "soc_status": "Calibrated via Lookup Table", "t": 31.2 },
          "inverter": { "v_ac": 220.1, "i_ac": 0.12, "p_ac": 26.4, "eff": 95.2 },
          "relay": { "fan": false, "lamp": true }
        }
      ]
    }
    ```

*   **Response (200 OK) - Jika `component=pv` (Hanya data PV):**
    ```json
    {
      "count": 2,
      "data": [
        {
          "timestamp": "2026-06-11T08:00:00Z",
          "pv": { "v": 18.4, "i": 2.1, "p": 38.6, "t": 52.3 }
        },
        {
          "timestamp": "2026-06-11T08:01:00Z",
          "pv": { "v": 18.2, "i": 2.0, "p": 36.4, "t": 52.5 }
        }
      ]
    }
    ```

*   **Response (200 OK) - Jika `component=battery` (Hanya data Baterai & SoC):**
    ```json
    {
      "count": 2,
      "data": [
        {
          "timestamp": "2026-06-11T08:00:00Z",
          "battery": { "v": 12.6, "i": 1.8, "p": 22.7, "soc": 78.5, "soc_status": "Calibrated via Lookup Table", "t": 31.2 }
        }
      ]
    }
    ```

---

### C. Ekspor Data Log ke CSV
Mengunduh file `.CSV` mentah untuk diolah mahasiswa di Excel.

*   **Endpoint:** `GET /api/v1/telemetry/export`
*   **Query Parameters:**
    *   `start_time` (string, ISO 8601): Wajib.
    *   `end_time` (string, ISO 8601): Wajib.
*   **Response (200 OK):**
    *   **Content-Type:** `text/csv`
    *   **Headers:** `Content-Disposition: attachment; filename="telemetry_log_20260611.csv"`
    *   **Body Content (Format File CSV):**
        ```csv
        Timestamp,PV_Voltage,PV_Current,PV_Power,PV_Temp,BAT_Voltage,BAT_Current,BAT_Power,BAT_SoC,BAT_SoC_Status,BAT_Temp,INV_VoltageAC,INV_CurrentAC,INV_PowerAC,INV_Eff,Relay_Fan,Relay_Lamp
        2026-06-11T08:00:00Z,18.40,2.10,38.60,52.3,12.60,1.80,22.70,78.5,Calibrated via Lookup Table,31.2,220.10,0.12,26.40,95.20,FALSE,TRUE
        2026-06-11T08:01:00Z,18.20,2.00,36.40,52.5,12.50,1.70,21.25,78.3,Coulomb Counting,31.3,219.80,0.12,26.30,94.80,FALSE,TRUE
        ```

---

### D. Kirim Log Sensor Baru (Dari MQTT Bridge Daemon ke Backend)
Digunakan oleh skrip jembatan di PC Lab untuk memasukkan data yang disubscribe dari MQTT ke PostgreSQL.

*   **Endpoint:** `POST /api/v1/telemetry`
*   **Request Body (JSON):**
    ```json
    {
      "timestamp": "2026-06-11T08:00:00Z",
      "pv": { "v": 18.4, "i": 2.1, "p": 38.6, "t": 52.3 },
      "battery": { "v": 12.6, "i": 1.8, "p": 22.7, "soc": 78.5, "soc_status": "Calibrated via Lookup Table", "t": 31.2 },
      "inverter": { "v_ac": 220.1, "i_ac": 0.12, "p_ac": 26.4, "eff": 95.2 },
      "relay": { "fan": false, "lamp": true }
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "status": "success",
      "message": "Data telemetry logged successfully",
      "id": 104928
    }
    ```

---

## 3. MQTT Topic Hierarchy & Payload Design

Komunikasi real-time latensi rendah (interval 1 detik) menggunakan protokol MQTT. 

### Hirarki Topik MQTT:
```text
laboratorium/scada/pv_kit/
├── telemetry        [Publish: ESP32]      -> Mengirim data sensor real-time
├── control/fan      [Subscribe: ESP32]    -> Menerima perintah sakelar Kipas AC
├── control/lamp     [Subscribe: ESP32]    -> Menerima perintah sakelar Lampu Pijar
└── status/relay     [Publish: ESP32]      -> Mengonfirmasi status relay terkini ke App
```

---

### A. Topik: `laboratorium/scada/pv_kit/telemetry`
*   **Pengirim (Pub):** ESP32 DevKitC V4  
*   **Penerima (Sub):** Aplikasi Mobile & Python Broker Daemon  
*   **Payload JSON:**
    ```json
    {
      "timestamp": "2026-06-11T15:05:00",
      "pv": {
        "v": 18.42,
        "i": 2.15,
        "p": 39.60,
        "t": 52.3
      },
      "battery": {
        "v": 12.60,
        "i": 1.80,
        "p": 22.68,
        "soc": 78.50,
        "soc_status": "Calibrated via Lookup Table",
        "t": 31.2
      },
      "inverter": {
        "v_ac": 220.10,
        "i_ac": 0.12,
        "p_ac": 26.40,
        "eff": 95.20
      },
      "relay": {
        "fan": false,
        "lamp": true
      }
    }
    ```

---

### B. Topik Kontrol Relay (Beban)
Digunakan oleh Aplikasi Mobile untuk mengubah keadaan relay AC.

#### 1. Kipas AC
*   **Topik:** `laboratorium/scada/pv_kit/control/fan`
*   **Pengirim (Pub):** Aplikasi Mobile (Setelah pop-up konfirmasi disetujui)
*   **Penerima (Sub):** ESP32
*   **Payload JSON:**
    ```json
    {
      "state": true
    }
    ```
    *(Keterangan: `true` untuk menyalakan/ON, `false` untuk mematikan/OFF)*

#### 2. Lampu Pijar
*   **Topik:** `laboratorium/scada/pv_kit/control/lamp`
*   **Pengirim (Pub):** Aplikasi Mobile (Setelah pop-up konfirmasi disetujui)
*   **Penerima (Sub):** ESP32
*   **Payload JSON:**
    ```json
    {
      "state": false
    }
    ```

---

### C. Topik: `laboratorium/scada/pv_kit/status/relay`
Umpan balik (feedback) instan dari ESP32 untuk memastikan bahwa perubahan relay benar-benar sukses terjadi di lapangan (mencegah salah sinkronisasi status UI di aplikasi).

*   **Pengirim (Pub):** ESP32 DevKitC V4 (Tiap kali ada perintah kontrol masuk & dieksekusi)
*   **Penerima (Sub):** Aplikasi Mobile
*   **Payload JSON:**
    ```json
    {
      "fan": true,
      "lamp": false,
      "timestamp": "2026-06-11T15:05:02"
    }
    ```

---

> **Catatan Validasi Payload (Pydantic / Dart Model):**
> Baik di Flutter (Dart class generator) maupun FastAPI (Pydantic Model), pastikan seluruh variabel angka menggunakan tipe data desimal/float (`double` di Dart, `float` di Python/Pydantic) karena fluktuasi data sensor sangat dinamis. Nilai boolean pada `relay` dipetakan langsung ke tipe data boolean di masing-masing bahasa pemrograman.
