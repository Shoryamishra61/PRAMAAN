# PRAMAAN / CARVE-FECL — PERFORMANCE & LOAD SATURATION TEST PLAN

> **Script**: `scripts/load_saturation_benchmark.py`  
> **Output Artifact**: `output/load_benchmark_results.json`  
> **Testing Ethos**: Measure accurately on real developer/CI hardware without exaggerating throughput or claiming distributed datacenter capacity on a local machine.

---

## 1. Test Objectives & Scope

1. Determine the maximum sustained throughput (RPS) of inbound Razorpay webhook ingestion.
2. Characterize latency percentiles (p50, p95, p99) under escalating concurrent writer load.
3. Quantify SQLite WAL mode write-lock contention under multi-threaded concurrency (1 to 16 workers).
4. Verify that under severe concurrency saturation, zero events are silently dropped or lost.

---

## 2. Tested Architecture & Hardware Profile

```text
Inbound Webhook ───► HMAC Authentication ───► Ingestion Pipeline ───► SQLite WAL (Durable Queue)
                                                                             │
                                                                       BEGIN IMMEDIATE
                                                                     (busy_timeout=5000ms)
```

- **Operating System**: Windows / Linux
- **Storage Mode**: SQLite 3 with Write-Ahead Logging (WAL) and `synchronous=NORMAL`.
- **Concurrency Isolation**: Transactions serialized via `BEGIN IMMEDIATE` to prevent deadlock.
- **Queue Semantics**: Inbound events and background `PROCESS_CASE` jobs committed in a single atomic transaction.

---

## 3. Concurrency & Throughput Benchmark Matrix

Empirical results from `scripts/load_saturation_benchmark.py` across 100 requests per concurrency tier:

| Worker Threads | Total Requests | Throughput (RPS) | p50 Latency (ms) | p95 Latency (ms) | Lock Errors | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1 Worker** | 100 | 106.8 RPS | 9.0 ms | 10.8 ms | 0 | PASSED |
| **2 Workers** | 100 | 87.0 RPS | 17.9 ms | 48.8 ms | 0 | PASSED |
| **4 Workers** | 100 | 120.5 RPS | 19.5 ms | 96.3 ms | 0 | PASSED |
| **8 Workers** | 100 | 118.9 RPS | 21.5 ms | 295.5 ms | 0 | PASSED |
| **16 Workers** | 100 | 100.1 RPS | 48.0 ms | 688.6 ms | 0 | PASSED |

---

## 4. Single-Node Scaling Boundary & Saturation Findings

1. **Throughput Ceiling**: Single-node SQLite achieves between 100 and 125 RPS sustained write throughput when persisting full payloads and scheduling background jobs.
2. **Graceful Queueing**: As concurrency scales from 4 to 16 worker threads, SQLite `busy_timeout=5000ms` completely absorbs lock contention without raising unhandled errors.
3. **P95 Latency Tradeoff**: At 16 concurrent workers, write serialization increases p95 latency to ~688 ms while maintaining 100% data integrity and zero lost updates.
4. **Production Architecture Recommendation**: For enterprise workloads exceeding 150 sustained writes/second, migrate the backing store to PostgreSQL while preserving the exact same domain contracts and idempotency invariants.
