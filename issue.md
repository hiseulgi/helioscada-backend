# HELIOSCADA Backend - Task Breakdown (Issue)

Berdasarkan `prd.md` dan `system_spec.md`, berikut adalah daftar tugas-tugas besar (Epic/Issues) untuk pengembangan backend aplikasi monitoring HELIOSCADA:

## 1. Setup Proyek & Infrastruktur
- [ ] Inisialisasi struktur proyek FastAPI (Python 3.13) mengikuti pola asinkron (mengacu pada modul `.agents/skills/fastapi-template`).
- [ ] Konfigurasi _dependency manager_ menggunakan `uv` (`pyproject.toml`) dengan package utama: `fastapi`, `uvicorn`, `sqlalchemy` (v2.0), `pydantic` (v2), `asyncpg`.
- [ ] Setup _environment variables_ (`.env`) untuk kredensial PostgreSQL dan konfigurasi broker MQTT.
- [ ] Buat file `docker-compose.yml` untuk mempermudah penyediaan database PostgreSQL dan Mosquitto MQTT Broker di PC lab.

## 2. Implementasi Database & Model (ORM)
- [ ] Setup koneksi database PostgreSQL secara asinkron menggunakan `asyncpg` dan konfigurasi *session management*.
- [ ] Buat model SQLAlchemy 2.0 untuk tabel `telemetry_logs` (kolom parameter sensor DC, AC, suhu, SoC baterai, status relay, dengan *index* pada `timestamp`).
- [ ] Buat model SQLAlchemy untuk tabel `control_logs` (pencatatan log aktuator).
- [ ] (Opsional) Setup Alembic untuk _database migrations_.

## 3. Pembuatan Schema Kontrak Data (Pydantic V2)
- [ ] Buat schema validasi payload masuk untuk data telemetri (berisi objek nested: `pv`, `battery`, `inverter`, `relay`).
- [ ] Buat schema response untuk `GET /health` (Status Server & DB).
- [ ] Buat schema response dinamis untuk `GET /api/v1/telemetry` yang bisa menyesuaikan filter `component` (seperti `pv`, `battery`, `inverter`, `all`).

## 4. Pengembangan API Endpoints (RESTful Routers)
- [ ] **`GET /health`**: Implementasi sistem pengecekan status kesiapan *service* dan koneksi database.
- [ ] **`POST /api/v1/telemetry`**: Implementasi endpoint *insert* log sensor baru ke dalam database.
- [ ] **`GET /api/v1/telemetry`**: Implementasi endpoint pengambil riwayat data dengan dukungan filter *query parameter* (`start_time`, `end_time`, `component`) serta logika kompresi data (*downsampling*) jika data terlalu besar.
- [ ] **`GET /api/v1/telemetry/export`**: Implementasi konversi data *time-series* dari database menjadi format file teks/CSV dan dikembalikan via `StreamingResponse` atau `FileResponse`.

## 5. Implementasi Daemon MQTT Bridge
- [ ] Buat skrip jembatan (Python Daemon) menggunakan library `paho-mqtt` atau `aiomqtt`.
- [ ] Setup fungsionalitas daemon untuk *subscribe* secara terus-menerus ke topik `laboratorium/scada/pv_kit/telemetry`.
- [ ] Tulis logika agar daemon mem-parsing JSON dari broker dan mengirimnya ke database (dengan *hit* ke `POST /api/v1/telemetry` atau simpan langsung ke *session* DB).

## 6. Testing & Verifikasi
- [ ] Isi tabel dengan data _dummy_ dan verifikasi *query execution time* untuk filter tanggal yang lebar.
- [ ] Cek endpoint CSV export untuk memastikan header dan baris nilainya formatnya sesuai standard.
- [ ] (Opsional) Buat unit test dasar menggunakan `pytest` dan `httpx` (TestClient) untuk fungsi-fungsi kritikal API.
