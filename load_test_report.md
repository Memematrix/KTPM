# Performance & Load Testing Report: Cinema Booking System

**Test Environment:** Kaggle Notebook Instance (4 vCPUs, 30 GB RAM)  
**Target Backend:** FastAPI + Uvicorn + SQLAlchemy (PostgreSQL / SQLite)  
**Benchmarking Tool:** Locust (Headless, 80 Concurrent Virtual Users, Ramp Rate: 4 users/sec, Duration: 120s)

---

## 1.  Summary

| Metric | Measured Value | Target / SLA | Status |
| :--- | :--- | :--- | :--- |
| **Total Requests Handled** | **1,525** | — | Completed |
| **Failed Requests** | **0 (0.0%)** | < 1.0% |  Passed |
| **Average Throughput** | **12.78 RPS** | > 100 RPS |  Below Capacity |
| **Peak Throughput** | **~17.0 RPS** (at $t = 20s$) | — | Plateaued |
| **Aggregate Median Latency** | **6,000 ms** (6.0 s) | < 200 ms |  Critical |
| **Aggregate p95 Latency** | **7,000 ms** (7.0 s) | < 500 ms |  Critical |
| **Host CPU Utilization** | **< 5% average** (Spike: 30% at boot) | 60% – 80% |Starvation |


### Detailed Test Results Table

| ID | Method | Endpoint / Name | Requests | Failures | Median (ms) | 95th % (ms) | RPS | Latency Classification |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 0 | `POST` | `00_Auth_Login` | 52 | 0 | 2,500 | 6,200 | 0.44 |Degraded |
| 1 | `POST` | `00_Auth_Register` | 52 | 0 | 6 | 9 | 0.44 |  Fast (< 10 ms) |
| 2 | `GET` | `01_HTML_Home` | 171 | 0 | 2 | 5 | 1.43 |  Fast (< 10 ms) |
| 3 | `GET` | `02_HTML_Movies` | 163 | 0 | 5,900 | 6,700 | 1.37 |  Critical (> 5s) |
| 4 | `GET` | `03_API_List_Movies` | 161 | 0 | 6,000 | 6,900 | 1.35 |  Critical (> 5s) |
| 5 | `GET` | `04_HTML_Movie_Detail` | 154 | 0 | 6,500 | 7,200 | 1.29 |  Critical (> 5s) |
| 6 | `GET` | `05_API_Movie_Detail` | 149 | 0 | 6,200 | 6,900 | 1.25 |  Critical (> 5s) |
| 7 | `GET` | `06_API_Movie_Reviews` | 136 | 0 | 6,700 | 7,300 | 1.14 |  Worst Performer (7.3s) |
| 8 | `GET` | `07_API_List_Showtimes` | 126 | 0 | 2 | 4 | 1.06 |  Fast (< 5 ms) |
| 9 | `GET` | `10_API_List_Screens` | 109 | 0 | 6,200 | 6,800 | 0.91 |  Critical (> 5s) |
| 10 | `GET` | `11_API_Screen_Seats` | 102 | 0 | 6,500 | 7,100 | 0.86 |  Critical (> 5s) |
| 11 | `GET` | `12_API_List_Food` | 93 | 0 | 6,300 | 7,000 | 0.78 |  Critical (> 5s) |
| 12 | `GET` | `Casual_GET_/` | 15 | 0 | 2 | 4 | 0.13 |  Fast (< 5 ms) |
| 13 | `GET` | `Casual_GET_/api/screens`| 6 | 0 | 5,900 | 6,500 | 0.05 |  Critical (> 5s) |
| 14 | `GET` | `Casual_GET_/food` | 11 | 0 | 5,700 | 6,800 | 0.09 |  Critical (> 5s) |
| 15 | `GET` | `Casual_GET_/health` | 10 | 0 | 2 | 8 | 0.08 |  Fast (< 10 ms) |
| 16 | `GET` | `Casual_GET_/movies` | 3 | 0 | 5,400 | 6,200 | 0.03 |  Critical (> 5s) |
| 17 | `GET` | `Casual_GET_/showtimes` | 12 | 0 | 5,800 | 6,900 | 0.10 |  Critical (> 5s) |
| **18** | **—** | **Aggregated Total** | **1,525** | **0** | **6,000** | **7,000** | **12.78** |  **System Bottlenecked** |