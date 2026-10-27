# Hệ thống bán vé xem phim

Bài tập lớn môn Kiến trúc phần mềm: xây dựng backend quản lý rạp và đặt vé xem phim bằng FastAPI, PostgreSQL.

## 1. Bài toán và phạm vi

Một rạp có nhiều phim, phòng, ghế và suất chiếu. Hệ thống cần liên kết chính xác **phim – suất chiếu – phòng – ghế**, hỗ trợ khách đặt vé kèm đồ ăn, đồng thời ngăn trùng lịch và trùng ghế trong cùng suất chiếu.

- **Khách chưa đăng nhập:** tra cứu phim, đánh giá, phòng, ghế, suất chiếu và đồ ăn; đăng ký, đăng nhập.
- **Khách hàng (`customer`):** tạo đơn đặt vé, xem và xóa đơn của mình; xem tài khoản, viết và xóa đánh giá của mình.
- **Quản trị viên (`admin`):** quản lý phim, phòng, ghế, suất chiếu, đồ ăn; xem và xóa mọi đơn, xóa đánh giá của người dùng khác.

**Đã có trong mã nguồn:** API tài khoản, phân quyền, quản lý dữ liệu rạp, tra cứu tình trạng ghế, tạo đơn cùng vé và đồ ăn, xem/xóa đơn, đánh giá phim.

**Chưa triển khai:** thanh toán trực tuyến, giữ ghế có thời hạn, tự động giải phóng đơn hết hạn và quy trình hủy vé/hoàn tiền. Đơn và vé mới có trạng thái mặc định `pending`; tạo đơn chưa đồng nghĩa đã thanh toán.

## 2. Nghiệp vụ chính

### 2.1. Tài khoản và quản lý rạp

Người dùng đăng ký → hệ thống kiểm tra tên trùng, băm mật khẩu và tạo tài khoản `customer` → đăng nhập nhận JWT → gửi `Authorization: Bearer <access_token>` khi gọi API cần xác thực. API quản trị kiểm tra thêm vai trò `admin`.

Quản trị viên tạo phim → tạo phòng và sức chứa → khai báo ghế → tạo suất chiếu theo phim, phòng, giờ bắt đầu/kết thúc và giá cơ bản; bổ sung danh mục đồ ăn. API kiểm tra phim/phòng tồn tại, sức chứa, vị trí ghế trùng, thời gian kết thúc sau bắt đầu và lịch chiếu không chồng lấn trong cùng phòng.

### 2.2. Tra cứu và đặt vé

1. Khách chọn phim và ngày để tìm suất chiếu; xem danh sách ghế cùng `is_available`. API tra cứu coi ghế có bản ghi vé trong suất là đã đặt.
2. Khách đã đăng nhập gửi `showtime_id`, danh sách `seat_ids` và đồ ăn kèm số lượng tới `POST /orders`.
3. Hệ thống kiểm tra suất tồn tại, ghế thuộc đúng phòng, ID ghế/món không lặp, món tồn tại và ghế chưa có vé `pending` hoặc `confirmed`.
4. Hệ thống tính **tổng tiền = giá cơ bản của suất × số ghế + tổng (giá món × số lượng)**. Hiện chưa có phụ thu theo loại ghế.
5. Đơn, vé và các dòng đồ ăn được ghi trong cùng một giao dịch. Giá vé và giá món tại thời điểm đặt được lưu vào chi tiết đơn; lỗi ràng buộc khi commit được rollback và trả `409`.
6. Khách xem danh sách/chi tiết đơn của mình; admin được xem mọi đơn. API xóa đơn cũng giới hạn theo quyền này.

`DELETE /orders/{order_id}` hiện thực hiện xóa đơn, chưa phải quy trình hủy có lưu lịch sử và hoàn tiền. Việc xóa vé liên quan, giải phóng ghế cần kiểm chứng với cấu hình khóa ngoại của database đang chạy; xem [lưu ý API](docs/api-reference.md#luu-y-don-hang).

### 2.3. Đánh giá phim

Người dùng đăng nhập gửi điểm 1–5 và bình luận cho phim tồn tại. Mọi người được xem đánh giá; chỉ tác giả hoặc admin được xóa. Hiện chưa yêu cầu đã mua vé và chưa giới hạn một đánh giá/người/phim.

## 3. Các vấn đề cần xử lý và yêu cầu kỹ thuật

- **Đặt trùng ghế khi có nhiều yêu cầu đồng thời:** kiểm tra trước khi đặt chưa đủ vì hai khách có thể cùng thấy ghế trống. Model đã khai báo unique `(showtime_id, seat_id)` và API có rollback khi lỗi ràng buộc. Cần xác nhận constraint đã có trên database thực tế và kiểm thử đồng thời trước khi kết luận cơ chế hoạt động đúng.
- **Lịch chiếu và sức chứa:** đã có kiểm tra tại API và unique vị trí ghế trong phòng. Kiểm tra chồng lịch/sức chứa chưa đủ bảo đảm an toàn khi nhiều yêu cầu ghi đồng thời; chưa tính thời gian nghỉ giữa các suất.
- **Xác thực và phân quyền:** dùng JWT, mật khẩu băm bằng bcrypt; kiểm tra vai trò và quyền sở hữu đơn/đánh giá. Bí mật cấu hình nằm trong `.env`, không đưa lên Git.
- **Toàn vẹn dữ liệu:** đơn và chi tiết phải được ghi cùng giao dịch; dùng khóa ngoại và ràng buộc duy nhất. Schema kiểm tra dữ liệu đầu vào, nhưng còn thiếu kiểm tra giá suất không âm, thời lượng suất so với phim và enum loại ghế ở request.
- **Hiệu năng:** cần phản hồi ổn định khi nhiều khách tra cứu/đặt vé; API danh sách hiện chưa phân trang. Repo có [báo cáo kiểm thử tải](load_test_report.md); các số đo chỉ phản ánh môi trường/kịch bản trong báo cáo, chưa chứng minh khả năng xử lý đặt vé đồng thời.

## 4. Kiến trúc, tổ chức mã nguồn và công nghệ

Hệ thống là **một ứng dụng FastAPI triển khai chung, chia mã nguồn theo module chức năng**, dùng chung PostgreSQL. Nghiệp vụ và truy vấn dữ liệu hiện chủ yếu nằm trong router; chưa tách tầng service/repository riêng.

```text
src/
  main.py                 # Khởi tạo ứng dụng, đăng ký router, vòng đời kết nối DB
  common/
    config.py             # Đọc cấu hình môi trường
    database.py           # Engine, session bất đồng bộ và Base của ORM
    auth/                 # JWT, băm mật khẩu, xác thực và kiểm tra vai trò
  modules/
    auth/                 # Tài khoản; router/schema phim và đánh giá
    scheduling/           # Phòng, ghế, suất chiếu; chứa cả model Movie và Ticket
    ordering/             # Đồ ăn, đơn hàng, chi tiết đồ ăn và nghiệp vụ đặt vé
```

Mỗi module có `routers/` để nhận và xử lý yêu cầu, `schemas.py` khai báo dữ liệu vào/ra, `models.py` ánh xạ bảng dữ liệu. Các module hiện có import chéo model. Luồng xử lý API: **request → xác thực/phân quyền (nếu cần) và kiểm tra schema → router xử lý nghiệp vụ → SQLAlchemy → PostgreSQL → response**.

- **Python 3.12+, FastAPI, Uvicorn:** ngôn ngữ, framework API và máy chủ ứng dụng.
- **SQLAlchemy Async, asyncpg, PostgreSQL:** ORM và truy cập database bất đồng bộ; có thể dùng PostgreSQL do Supabase cung cấp.
- **Pydantic, pydantic-settings:** kiểm tra request/response và đọc cấu hình.
- **PyJWT, Passlib, bcrypt:** JWT và băm mật khẩu; ứng dụng tự quản lý tài khoản, không dùng Supabase Auth.
- **Docker, Docker Compose:** đóng gói dịch vụ API; database được cung cấp riêng.

## 5. Chạy nhanh và tài liệu API

Xem [hướng dẫn cấu hình và Docker](docs/setup.md).

API gồm các nhóm `/api/auth`, `/api/movies`, `/api/reviews`, `/api/screens`, `/api/seats`, `/api/showtimes`, `/food` và `/orders`. Dữ liệu nghiệp vụ dùng JSON, ID dùng UUID; API cần đăng nhập dùng Bearer JWT.

- [Tham chiếu endpoint, đầu vào/đầu ra và mã lỗi](docs/api-reference.md).
- Khi API đang chạy: [Swagger UI](http://localhost:8000/docs), [ReDoc](http://localhost:8000/redoc), [OpenAPI JSON](http://localhost:8000/openapi.json).
- [Health check](http://localhost:8000/health): kiểm tra API phản hồi, không kiểm tra kết nối database.
