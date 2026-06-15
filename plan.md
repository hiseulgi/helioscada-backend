# HELIOSCADA Backend - Micro-Step Implementation Plan

Dokumen ini berisi langkah-langkah teknis mikro dari `issue.md` agar dapat dieksekusi satu per satu oleh AI. Setiap tahap dibagi menjadi sub-klaster (Step) yang lebih spesifik.

## Tahap 1: Setup Proyek & Infrastruktur Dasar

### Step 1.1: Inisialisasi Struktur Proyek
- [ ] Buat direktori utama: `src/backend/app`, `src/backend/bridge`, dan `tests`.
- [ ] Jalankan inisialisasi *dependency manager* menggunakan `uv init` dengan target Python 3.13.
- [ ] Buat struktur folder di dalam `app`: `api`, `core`, `db`, `models`, `schemas`, `services`.

### Step 1.2: Instalasi Dependencies & Konfigurasi Environment
- [ ] Konfigurasikan `pyproject.toml` dengan dependencies utama: `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `pydantic-settings`, `pydantic`, `paho-mqtt`.
- [ ] Buat file `src/backend/app/core/config.py` yang mendefinisikan class `Settings` berbasis `pydantic-settings` untuk *load environment variables*.
- [ ] Buat file `.env.example` yang mencakup variabel: `DATABASE_URL`, `MQTT_BROKER`, `MQTT_PORT`, dll.

### Step 1.3: Setup Docker & External Services
- [ ] Buat file konfigurasi broker MQTT: `mosquitto.conf` (izinkan koneksi anonim untuk keperluan lab lokal).
- [ ] Buat `docker-compose.yml` yang berisi *services*: `db` (PostgreSQL), `mosquitto` (Eclipse Mosquitto).
- [ ] Tambahkan konfigurasi `api` dan `bridge` ke dalam `docker-compose.yml` (menggunakan `Dockerfile` atau run command lokal untuk dev).

---

## Tahap 2: Setup Database & SQLAlchemy Models

### Step 2.1: Inisialisasi Koneksi Database
- [ ] Buat file `src/backend/app/db/session.py`.
- [ ] Buat asinkron SQLAlchemy engine menggunakan `create_async_engine`.
- [ ] Buat session factory menggunakan `async_sessionmaker`.

### Step 2.2: Pembuatan Base Model & Skrip Inisiasi
- [ ] Buat file declarative base: `src/backend/app/models/base.py`.
- [ ] Buat skrip `src/backend/app/db/init_db.py` untuk mengeksekusi `Base.metadata.create_all` saat *startup*.

### Step 2.3: Pembuatan Tabel Data Telemetri & Kontrol
- [ ] Buat file `src/backend/app/models/telemetry.py`.
- [ ] Deklarasikan class model `TelemetryLog` dengan kolom PV, Battery, Inverter, Relay.
- [ ] Tambahkan index pada kolom `timestamp` di `TelemetryLog`.
- [ ] Buat file `src/backend/app/models/control.py`.
- [ ] Deklarasikan class model `ControlLog` untuk riwayat aktuasi alat.

---

## Tahap 3: Pembuatan Pydantic Schemas (Kontrak API)

### Step 3.1: Schema Health Check & Komponen Dasar
- [ ] Buat file `src/backend/app/schemas/health.py` untuk schema respons Health Check.
- [ ] Buat file `src/backend/app/schemas/telemetry.py`.
- [ ] Definisikan nested schema: `PVData`, `BatteryData`, `InverterData`, `RelayData`.

### Step 3.2: Schema Input & Output Telemetri
- [ ] Definisikan schema validasi `TelemetryLogCreate` (untuk payload MQTT masuk).
- [ ] Definisikan schema respons serialisasi `TelemetryLogResponse`.
- [ ] Definisikan schema untuk *dynamic filtering* yang opsional memuat subset data komponen berdasarkan argumen *query*.

---

## Tahap 4: Pengembangan API Endpoints & Logic

### Step 4.1: Dependency Injection & Health Router
- [ ] Buat file `src/backend/app/api/deps.py` yang berisi generator `get_db()` asinkron.
- [ ] Buat file router: `src/backend/app/api/routers/health.py`.
- [ ] Implementasikan endpoint `GET /health` untuk memverifikasi DB connection.

### Step 4.2: Router Input Telemetri (POST)
- [ ] Buat file router: `src/backend/app/api/routers/telemetry.py`.
- [ ] Implementasikan endpoint `POST /api/v1/telemetry`.
- [ ] Buat fungsi service di `src/backend/app/services/telemetry.py` untuk menangani insert log data baru ke database.

### Step 4.3: Router Historis Telemetri (GET & Downsampling)
- [ ] Implementasikan logic `GET /api/v1/telemetry` di dalam file router telemetri.
- [ ] Tambahkan validasi *query params*: `start_time`, `end_time`, `component`.
- [ ] Implementasikan logika algoritma kompresi data (*downsampling*) sederhana pada level *service* bila titik data melewati ambang batas.

### Step 4.4: Router Export Data (CSV)
- [ ] Tambahkan logika endpoint `GET /api/v1/telemetry/export`.
- [ ] Gunakan `StreamingResponse` FastAPI untuk menyalurkan *CSV generator* berdasarkan query tanggal.

### Step 4.5: Registrasi App
- [ ] Buat file *main entrypoint*: `src/backend/app/main.py`.
- [ ] Registrasikan seluruh router yang telah dibuat ke instance *FastAPI application*.

---

## Tahap 5: Implementasi MQTT Bridge Daemon

### Step 5.1: Setup Kerangka Daemon
- [ ] Buat file *main* untuk bridge: `src/backend/bridge/main.py`.
- [ ] Inisialisasi struktur `paho-mqtt` atau `aiomqtt` client.
- [ ] Konfigurasikan logika koneksi ke MQTT broker beserta fungsi *reconnect*.

### Step 5.2: Subscribe & Parsing Data
- [ ] Definisikan fungsi logika *subscribe* ke topik `laboratorium/scada/pv_kit/telemetry`.
- [ ] Implementasikan *callback* `on_message` untuk melakukan konversi/parsing format JSON dari payload ESP32.

### Step 5.3: Sinkronisasi ke Database
- [ ] Implementasikan pengiriman data yang di-parsing via HTTP POST ke endpoint `POST /api/v1/telemetry` FastAPI (menggunakan `httpx` asinkron).
- [ ] Lakukan penanganan error dasar jika API sedang tidak dapat dijangkau.

---

## Tahap 6: Testing & Finishing

### Step 6.1: Menyiapkan Alat Pengujian
- [ ] Buat file skrip: `tests/dummy_publisher.py`.
- [ ] Tulis logika *dummy loop* yang menerbitkan payload MQTT tiruan secara berkala untuk simulasi kit PV.

### Step 6.2: Verifikasi Fungsionalitas Menyeluruh
- [ ] *Up* seluruh layanan dengan perintah `docker compose up`.
- [ ] Jalankan skrip *dummy publisher* untuk mensimulasikan aliran data.
- [ ] Validasi *insertion* ke tabel PostgreSQL (apakah data masuk sesuai jumlah publish).
- [ ] Verifikasi ketersediaan dan akurasi file *export* via panggilan HTTP/curl ke endpoint CSV.

### Step 6.3: Dokumentasi
- [ ] Perbarui `README.md` repositori backend dengan panduan eksekusi `uv run` & `docker compose`.
