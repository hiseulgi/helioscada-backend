# Code Review Report: HELIOSCADA Backend

**Date:** June 15, 2026
**Reviewer:** Antigravity (AI Code Reviewer)
**Scope:** Backend Services (FastAPI, MQTT Bridge, Database Models, Pytest Suite)

---

## 📊 Review Summary

The codebase demonstrates a solid, modern architectural foundation utilizing asynchronous Python (FastAPI, SQLAlchemy 2.0). The codebase is DRY, clean, and has excellent test coverage (87%). The usage of `Pydantic` for schema validation and `aiosqlite`/`asyncpg` for non-blocking DB operations is commendable. 

However, there are several critical areas requiring attention before deploying to a production environment, specifically regarding **API Security**, **Memory Scaling (OOM risks)**, and **Fault Tolerance** in the MQTT daemon.

---

## 🔒 Security Review

### 1. Missing Authentication & Authorization
**Issue:** The REST API endpoints (`POST /api/v1/telemetry`, `GET /api/v1/telemetry`, and `/export`) are completely unauthenticated. Anyone with network access can ingest fake data or scrape historical logs.
**Suggested fix:** 
- Implement **API Key Authentication** (via headers) for the `POST /telemetry` endpoint so only the authorized MQTT Bridge can ingest data.
- Implement **JWT/OAuth2** for the frontend application accessing `GET` endpoints.

### 2. Overly Permissive CORS Policy
**Issue:** `src/backend/app/main.py` configures CORS to allow all origins (`allow_origins=["*"]`).
**Current code:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    ...
)
```
**Suggested fix:** Bind origins to an environment variable.
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.settings.ALLOWED_ORIGINS, # e.g., ["http://localhost:3000"]
    ...
)
```
**Why:** Prevents malicious websites from making unauthorized cross-origin requests to your API.

---

## ⚡ Performance & Scalability Review

### 1. Out-Of-Memory (OOM) Risk in Downsampling Logic
**Issue:** In `src/backend/app/services/telemetry.py` (`get_telemetry_history`), the code fetches *all* records into Python memory before applying the downsampling slice. If a user queries 1 year of data (e.g., millions of rows), `db.scalars(query).all()` will crash the server.
**Current code:**
```python
    result = await db.scalars(query)
    records = result.all() # ⚠️ DANGER: Loads everything into RAM
    # ... downsampling array slicing ...
```
**Suggested fix:** 
- **Option A:** Limit the maximum date range allowed per query (e.g., maximum 7 days).
- **Option B:** Push the downsampling logic to the database layer using PostgreSQL Window Functions (`ROW_NUMBER() OVER(...)`) or time-bucket aggregation (`date_trunc`).

### 2. Uncapped CSV Export
**Issue:** The `/export` endpoint streams data efficiently (avoiding memory leaks), but there is no limit on how much data can be requested. A malicious user could request 10 years of data, tying up database connections and network bandwidth for hours.
**Suggested fix:** Impose a hard limit on the date range (e.g., `if (end_time - start_time).days > 31: raise HTTPException(400)`).

---

## 🏗️ Architecture & Maintainability

### 1. MQTT Bridge Data Loss (No Retry Mechanism)
**Issue:** In `src/backend/bridge/main.py`, if the API server is temporarily down, the HTTP request fails, an error is printed, and the telemetry message is permanently dropped.
**Current code:**
```python
    except Exception as e:
        logger.error(f"Failed to push to API: {e}")
        # Message is lost forever
```
**Suggested fix:** 
Implement a retry loop with exponential backoff or write failed payloads to a local Dead Letter Queue (DLQ) file/SQLite db until the API becomes available again.

### 2. Graceful Shutdown in MQTT Bridge
**Issue:** The MQTT bridge uses an infinite loop (`while True: await queue.get()`) but does not listen for OS termination signals (SIGINT/SIGTERM) to shut down gracefully and disconnect the MQTT client cleanly.
**Suggested fix:** Register signal handlers via `asyncio.get_running_loop().add_signal_handler()` to cancel the task and call `client.disconnect()`.

---

## ✅ Code Quality & Tests

**Nice! Excellent Test Suite Implementation**
This is great because the unit tests utilize in-memory SQLite (`aiosqlite`), preventing the need for complex dockerized test databases. The fixtures are well-isolated, and the HTTPX AsyncClient overrides the database dependency cleanly.

**Quality Checklist Verification:**
- [x] Input Validation (Pydantic handles this perfectly)
- [x] SQL Injection (Safe: SQLAlchemy ORM utilized exclusively)
- [x] Naming Conventions (Clear, Pythonic `snake_case`)
- [x] DRY Principle (Schemas and Models are well abstracted)

---

## 🎯 Action Items (Next Steps)

1. **High Priority:** Restrict CORS origins in `main.py` via `.env`.
2. **High Priority:** Add a maximum date-range limit validator to both `GET /telemetry` and `GET /telemetry/export` endpoints to prevent database/memory overload.
3. **Medium Priority:** Add API Key authentication for the ingestion endpoint.
4. **Low Priority:** Implement a retry/DLQ mechanism in the MQTT Bridge daemon.
