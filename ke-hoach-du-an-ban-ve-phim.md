# Kế hoạch dự án: Hệ thống bán vé xem phim

## 1. Nguyên tắc chia việc

Mục tiêu: **chia theo module dọc (vertical slice)** — mỗi người sở hữu trọn vẹn 1 nhóm bảng từ API → Service → Repository, để code không đè lên nhau. Cross-module chỉ được phép **đọc** dữ liệu qua repository của chính người đó, không ai sửa file của người khác.

| Người | Module | Bảng sở hữu (ghi) |
|---|---|---|
| **A** | Auth & Catalog | `users`, `movies`, `reviews` |
| **B** | Scheduling | `screens`, `seats`, `showtimes` |
| **C** | Ordering | `food`, `orders`, `tickets`, `order_food` |

Người C cần **đọc** dữ liệu từ `movies` (Person A) và `seats`/`showtimes` (Person B) khi tạo đơn hàng — nhưng viết truy vấn đọc trong repository riêng của mình (module Ordering), không đụng file của A/B.

### Cấu trúc thư mục đề xuất (áp dụng cho bất kỳ framework nào)
```
src/
  common/            # auth middleware, config, base response, DB connection — làm chung ở Sprint 0
  modules/
    auth/            # Person A
    catalog/         # Person A (movies, reviews)
    scheduling/      # Person B (screens, seats, showtimes)
    ordering/        # Person C (food, orders, tickets)
```
Mỗi module tự có `controller/route`, `service`, `repository` riêng — không import chéo service, chỉ import chéo **repository (read-only)** khi cần.

Nếu dùng NestJS, cấu trúc module có sẵn khớp gần như 1-1 với cách chia này — rất đáng cân nhắc.

---

## 2. Danh sách API theo module

### Module Auth & Catalog — Person A

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| POST | `/auth/register` | Không | Đăng ký tài khoản |
| POST | `/auth/login` | Không | Đăng nhập, trả JWT |
| GET | `/auth/me` | ✅ | Thông tin user hiện tại |
| GET | `/movies` | Không | Danh sách phim (filter, search) |
| GET | `/movies/:id` | Không | Chi tiết phim |
| POST | `/movies` | ✅ (admin) | Thêm phim |
| PUT | `/movies/:id` | ✅ (admin) | Sửa phim |
| DELETE | `/movies/:id` | ✅ (admin) | Xoá phim |
| GET | `/movies/:id/reviews` | Không | Danh sách đánh giá phim |
| POST | `/movies/:id/reviews` | ✅ | Viết đánh giá |
| DELETE | `/reviews/:id` | ✅ (chủ review/admin) | Xoá đánh giá |

### Module Scheduling — Person B

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| GET | `/screens` | Không | Danh sách phòng chiếu |
| POST | `/screens` | ✅ (admin) | Tạo phòng chiếu |
| DELETE | `/screens/:id` | ✅ (admin) | Xoá phòng chiếu |
| GET | `/screens/:id/seats` | Không | Sơ đồ ghế của phòng |
| POST | `/screens/:id/seats` | ✅ (admin) | Tạo hàng loạt ghế cho phòng |
| DELETE | `/seats/:id` | ✅ (admin) | Xoá ghế |
| GET | `/showtimes?movie_id=&date=` | Không | Danh sách suất chiếu |
| GET | `/showtimes/:id` | Không | Chi tiết suất chiếu + tình trạng ghế (còn/đã đặt) |
| POST | `/showtimes` | ✅ (admin) | Tạo suất chiếu |
| DELETE | `/showtimes/:id` | ✅ (admin) | Xoá suất chiếu |

> Endpoint `GET /showtimes/:id` cần join `seats` + `tickets` để trả trạng thái từng ghế — logic này nằm trong module Scheduling vì nó chỉ đọc `tickets` (không ghi).

### Module Ordering — Person C

| Method | Endpoint | Auth | Mô tả |
|---|---|---|---|
| GET | `/food` | Không | Danh sách đồ ăn/nước |
| POST | `/food` | ✅ (admin) | Thêm món |
| DELETE | `/food/:id` | ✅ (admin) | Xoá món |
| POST | `/orders` | ✅ | Đặt vé: chọn `showtime_id`, danh sách `seat_id`, danh sách food+quantity → tạo `order` + `tickets` + `order_food` trong 1 transaction |
| GET | `/orders` | ✅ | Lịch sử đơn của user (admin xem tất cả) |
| GET | `/orders/:id` | ✅ (chủ đơn/admin) | Chi tiết đơn |
| DELETE | `/orders/:id` | ✅ (chủ đơn/admin) | Huỷ đơn (nhả ghế) |

**Lưu ý bắt buộc xử lý ở đây:** khi `POST /orders`, phải kiểm tra ghế chưa bị đặt trùng cho cùng `showtime_id` **trong transaction** (SELECT ... FOR UPDATE hoặc constraint), nếu không sẽ có race condition khi 2 người đặt cùng ghế cùng lúc. Đề xuất thêm **unique constraint `(showtime_id, seat_id)`** trên bảng `tickets` — schema hiện tại chưa có, nên bổ sung.

---

## 3. Lộ trình phát triển (đề xuất 5-6 tuần)

### Sprint 0 — Nền tảng chung (Tuần 1, cả 3 người cùng làm nửa buổi)
- Chọn framework (gợi ý: NestJS/Express + Prisma nếu Node, hoặc Spring Boot nếu Java — miễn khớp yêu cầu "tầng nghiệp vụ không import framework web/DB").
- Tạo repo GitHub, thống nhất branch convention (`feature/auth`, `feature/scheduling`, `feature/ordering`).
- Setup Docker + docker-compose (app + Postgres).
- Person A dựng khung `auth middleware` (JWT verify + role guard) làm nền cho cả nhóm dùng — chốt interface (`req.user.id`, `req.user.role`) ngay từ đầu để B, C không phải sửa lại sau.
- Migrate schema DB đã thiết kế, seed dữ liệu mẫu.
- Khung OpenAPI (Swagger) rỗng, mỗi người tự thêm spec module mình sau.

**Deliverable:** service chạy được, `/health` trả 200, đăng nhập thử được, Docker build thành công.

### Sprint 1 — CRUD cơ bản từng module (Tuần 2)
- A: hoàn thiện đăng ký/đăng nhập, CRUD `movies`.
- B: CRUD `screens`, `seats`.
- C: CRUD `food`.

**Deliverable:** 3 module chạy độc lập, có thể demo riêng từng phần, đã có test thủ công qua Postman/Swagger.

### Sprint 2 — Nghiệp vụ lõi (Tuần 3)
- A: `reviews` (viết/xoá đánh giá).
- B: `showtimes` CRUD + endpoint trả tình trạng ghế theo suất chiếu.
- C: luồng đặt vé `POST /orders` (transaction, chống trùng ghế, tính `total_amount`), `GET/DELETE /orders`.

**Deliverable:** luồng đặt vé end-to-end chạy được (chọn phim → chọn suất → chọn ghế → chọn đồ ăn → tạo đơn).

### Sprint 3 — Tích hợp & tài liệu (Tuần 4)
- Ghép 3 module vào 1 service hoàn chỉnh, kiểm tra không có import chéo sai tầng.
- Hoàn thiện Swagger đầy đủ (mỗi người tự viết spec module mình).
- Viết `README.md`: kiến trúc (sơ đồ tầng), đặc tả API, hướng dẫn chạy Docker.
- Rà soát lại: đúng phân tầng API → Service → Repository, service không import ORM/web framework.

**Deliverable:** repo hoàn chỉnh, README đầy đủ, Docker chạy 1 lệnh.

### Sprint 4 — Kiểm thử tải & chuẩn bị Pha 2 (Tuần 5)
- Viết script load test (k6/locust/Artillery) chạy trên Kaggle CPU, tập trung vào endpoint `POST /orders` (điểm nóng nhất, dễ race condition) và `GET /showtimes/:id`.
- Ghi nhận kết quả: latency, throughput, lỗi khi concurrent.
- Từ kết quả, phác thảo đề xuất Pha 2 (ví dụ: cache cho `GET /movies`, `GET /showtimes`; connection pooling; hàng đợi cho tạo đơn; index DB cho `tickets(showtime_id, seat_id)`).

**Deliverable:** báo cáo load test + đề xuất kiến trúc cải tiến cho Pha 2.

---

## 4. Điểm cần thống nhất sớm giữa 3 người (để tránh conflict về sau)

1. Format response chung (VD: `{ data, error }`) — chốt ở Sprint 0.
2. Cách middleware auth gắn `user` vào request — chốt ở Sprint 0, cả 3 dùng chung.
3. Naming convention cho DTO/schema request-response.
4. Ai review PR của ai — gợi ý: A review B, B review C, C review A (round-robin) để không ai chỉ tự merge code mình.
