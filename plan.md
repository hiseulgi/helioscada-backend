# HELIOSCADA Backend - Micro-Step Implementation Plan

Dokumen ini berisi langkah-langkah teknis mikro dari `issue.md` agar dapat dieksekusi satu per satu oleh AI. Setiap tahap dibagi menjadi sub-klaster (Step) yang lebih spesifik.

## Tahap 1: Setup Proyek & Infrastruktur Dasar

### Step 1.1: Inisialisasi Struktur Proyek
- [x] Buat direktori utama: `src/backend/app`, `src/backend/bridge`, dan `tests`.
- [x] Jalankan inisialisasi *dependency manager* menggunakan `uv init` dengan target Python 3.13.
- [x] Buat struktur folder di dalam `app`: `api`, `core`, `db`, `models`, `schemas`, `services`.

### Step 1.2: Instalasi Dependencies & Konfigurasi Environment
- [x] Konfigurasikan `pyproject.toml` dengan dependencies utama: `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `pydantic-settings`, `pydantic`, `paho-mqtt`.
- [x] Buat file `src/backend/app/core/config.py` yang mendefinisikan class `Settings` berbasis `pydantic-settings` untuk *load environment variables*.
- [x] Buat file `.env.example` yang mencakup variabel: `DATABASE_URL`, `MQTT_BROKER`, `MQTT_PORT`, dll.

### Step 1.3: Setup Docker & External Services
- [x] Buat file konfigurasi broker MQTT: `mosquitto.conf` (izinkan koneksi anonim untuk keperluan lab lokal).
- [x] Buat `docker-compose.yml` yang berisi *services*: `db` (PostgreSQL), `mosquitto` (Eclipse Mosquitto).
- [x] Tambahkan konfigurasi `api` dan `bridge` ke dalam `docker-compose.yml` (menggunakan `Dockerfile` atau run command lokal untuk dev).

---

## Tahap 2: Setup Database & SQLAlchemy Models

### Step 2.1: Inisialisasi Koneksi Database
- [x] Buat file `src/backend/app/db/session.py`.
- [x] Buat asinkron SQLAlchemy engine menggunakan `create_async_engine`.
- [x] Buat session factory menggunakan `async_sessionmaker`.

### Step 2.2: Pembuatan Base Model & Skrip Inisiasi
- [x] Buat file declarative base: `src/backend/app/models/base.py`.
- [x] Buat skrip `src/backend/app/db/init_db.py` untuk mengeksekusi `Base.metadata.create_all` saat *startup*.

### Step 2.3: Pembuatan Tabel Data Telemetri & Kontrol
- [x] Buat file `src/backend/app/models/telemetry.py`.
- [x] Deklarasikan class model `TelemetryLog` dengan kolom PV, Battery, Inverter, Relay.
- [x] Tambahkan index pada kolom `timestamp` di `TelemetryLog`.
- [x] Buat file `src/backend/app/models/control.py`.
- [x] Deklarasikan class model `ControlLog` untuk riwayat aktuasi alat.

---

## Tahap 3: Pembuatan Pydantic Schemas (Kontrak API)

### Step 3.1: Schema Health Check & Komponen Dasar
- [x] Buat file `src/backend/app/schemas/health.py` untuk schema respons Health Check.
- [x] Buat file `src/backend/app/schemas/telemetry.py`.
- [x] Definisikan nested schema: `PVData`, `BatteryData`, `InverterData`, `RelayData`.

### Step 3.2: Schema Input & Output Telemetri
- [x] Definisikan schema validasi `TelemetryLogCreate` (untuk payload MQTT masuk).
- [x] Definisikan schema respons serialisasi `TelemetryLogResponse`.
- [x] Definisikan schema untuk *dynamic filtering* yang opsional memuat subset data komponen berdasarkan argumen *query*.

---

## Tahap 4: Pengembangan API Endpoints & Logic

### Step 4.1: Dependency Injection & Health Router
- [x] Buat file `src/backend/app/api/deps.py` yang berisi generator `get_db()` asinkron.
- [x] Buat file router: `src/backend/app/api/routers/health.py`.
- [x] Implementasikan endpoint `GET /health` untuk memverifikasi DB connection.

### Step 4.2: Router Input Telemetri (POST)
- [x] Buat file router: `src/backend/app/api/routers/telemetry.py`.
- [x] Implementasikan endpoint `POST /api/v1/telemetry`.
- [x] Buat fungsi service di `src/backend/app/services/telemetry.py` untuk menangani insert log data baru ke database.

### Step 4.3: Router Historis Telemetri (GET & Downsampling)
- [x] Implementasikan logic `GET /api/v1/telemetry` di dalam file router telemetri.
- [x] Tambahkan validasi *query params*: `start_time`, `end_time`, `component`.
- [x] Implementasikan logika algoritma kompresi data (*downsampling*) sederhana pada level *service* bila titik data melewati ambang batas.

### Step 4.4: Router Export Data (CSV)
- [x] Tambahkan logika endpoint `GET /api/v1/telemetry/export`.
- [x] Gunakan `StreamingResponse` FastAPI untuk menyalurkan *CSV generator* berdasarkan query tanggal.

### Step 4.5: Registrasi App
- [x] Buat file *main entrypoint*: `src/backend/app/main.py`.
- [x] Registrasikan seluruh router yang telah dibuat ke instance *FastAPI application*.

---

## Tahap 5: Implementasi MQTT Bridge Daemon

### Step 5.1: Setup Kerangka Daemon
- [x] Buat file *main* untuk bridge: `src/backend/bridge/main.py`.
- [x] Inisialisasi struktur `paho-mqtt` atau `aiomqtt` client.
- [x] Konfigurasikan logika koneksi ke MQTT broker beserta fungsi *reconnect*.

### Step 5.2: Subscribe & Parsing Data
- [x] Definisikan fungsi logika *subscribe* ke topik `laboratorium/scada/pv_kit/telemetry`.
- [x] Implementasikan *callback* `on_message` untuk melakukan konversi/parsing format JSON dari payload ESP32.

### Step 5.3: Sinkronisasi ke Database
- [x] Implementasikan pengiriman data yang di-parsing via HTTP POST ke endpoint `POST /api/v1/telemetry` FastAPI (menggunakan `httpx` asinkron).
- [x] Lakukan penanganan error dasar jika API sedang tidak dapat dijangkau.

---

## Tahap 6: Testing & Finishing

### Step 6.1: Menyiapkan Alat Pengujian
- [x] Buat file skrip: `tests/dummy_publisher.py`.
- [x] Tulis logika *dummy loop* yang menerbitkan payload MQTT tiruan secara berkala untuk simulasi kit PV.

### Step 6.2: Verifikasi Fungsionalitas Menyeluruh
- [x] *Up* seluruh layanan dengan perintah `docker compose up`.
- [x] Jalankan skrip *dummy publisher* untuk mensimulasikan aliran data.
- [x] Validasi *insertion* ke tabel PostgreSQL (apakah data masuk sesuai jumlah publish).
- [x] Verifikasi ketersediaan dan akurasi file *export* via panggilan HTTP/curl ke endpoint CSV.

### Step 6.3: Unit Testing (pytest)
- [x] Tambahkan dependensi testing (`pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`) via `uv`.
- [x] Buat file konfigurasi testing (update `pyproject.toml` dengan konfigurasi pytest & coverage).
- [x] Buat file `tests/conftest.py` untuk mendefinisikan *fixtures*:
  - [x] `db_session`: In-memory SQLite asinkron yang selalu bersih di tiap *function scope*.
  - [x] `test_client`: `httpx.AsyncClient` dengan *dependency override* untuk `get_db`.
- [x] Buat `tests/test_api_health.py` (Pengujian Endpoint `/health`):
  - [x] *Success*: Database terhubung -> respons `200 OK`, `status: healthy`, `database: connected`.
  - [x] *Failure*: Database putus (mocking `db.execute` exception) -> respons `503 Service Unavailable`, `status: unhealthy`, `database: disconnected`.
- [x] Buat `tests/test_api_telemetry_post.py` (Pengujian Endpoint `POST /api/v1/telemetry`):
  - [x] *Success*: Payload JSON valid lengkap -> tersimpan ke DB, respons `201 Created` dengan `id`.
  - [x] *Success*: Payload JSON valid tanpa `timestamp` -> tersimpan dengan *default timestamp* server, respons `201 Created`.
  - [x] *Failure*: Payload cacat (misal tipe data salah atau format JSON rusak) -> respons `422 Unprocessable Entity`.
  - [x] *Failure*: Komponen wajib hilang (misal tidak ada objek `pv` di payload) -> respons `422 Unprocessable Entity`.
- [x] Buat `tests/test_api_telemetry_get.py` (Pengujian Endpoint `GET /api/v1/telemetry`):
  - [x] *Success*: Query rentang waktu valid -> mengembalikan daftar telemetri terurut kronologis sesuai jumlah yang disisipkan.
  - [x] *Success*: Uji *Dynamic Component Filtering* (`component="pv"`) -> respons JSON HANYA memuat kolom `timestamp` dan `pv` (kolom lain hilang/ter-*exclude*).
  - [x] *Success*: Uji *Downsampling* algoritma -> saat record melebih batas `downsample_limit=5`, pastikan respons dipotong rapi menjadi maksimal 5 elemen berjarak.
  - [x] *Failure*: Memanggil tanpa query params `start_time`/`end_time` -> respons `422 Unprocessable Entity`.
- [x] Buat `tests/test_api_telemetry_export.py` (Pengujian Endpoint `GET /api/v1/telemetry/export`):
  - [x] *Success*: Mengembalikan *StreamingResponse* berupa CSV -> verifikasi `Content-Type: text/csv`, header kolom tepat, tipe bool menjadi `TRUE`/`FALSE`.
  - [x] *Failure*: Parameter waktu tidak ada -> respons `422 Unprocessable Entity`.
- [x] Jalankan pengujian `pytest --cov=src` dan hasilkan laporan cakupan kode (target coverage min. 80%).

### Step 6.4: Dokumentasi
- [x] Perbarui `README.md` repositori backend dengan panduan eksekusi `uv run` & `docker compose`.
