# Tham chiếu API

[Quay lại README](../README.md). Tài liệu này mô tả API nghiệp vụ theo mã nguồn hiện tại. Đây là tài liệu Markdown bổ sung, không phải file đặc tả OpenAPI JSON/YAML được lưu trong repo.

Base URL: `http://localhost:8000`. Body dùng JSON; các ID là UUID, ngày dùng `YYYY-MM-DD`, ngày giờ dùng ISO 8601. Trường có dấu `?` là tùy chọn; các trường còn lại là bắt buộc, trừ body cập nhật phim.

API yêu cầu đăng nhập sử dụng header `Authorization: Bearer <access_token>`; quyền **Admin** tương ứng vai trò `admin`. Xem schema và thử request tại [Swagger UI](http://localhost:8000/docs).

Đăng nhập còn đặt cookie `access_token` có `HttpOnly`, `SameSite=Lax`, phạm vi `/showtimes` và `Secure` khi dùng HTTPS. Trang HTML `GET /showtimes/{showtime_id}` đọc cookie này và vẫn yêu cầu vai trò `admin`; API tiếp tục dùng Bearer token. Sau khi cập nhật từ phiên bản chỉ dùng localStorage, cần đăng xuất rồi đăng nhập lại để nhận cookie.

| Chức năng | Method và endpoint | Quyền | Đầu vào | Thành công / Đầu ra | Lỗi nghiệp vụ |
| --- | --- | --- | --- | --- | --- |
| Đăng ký | `POST /api/auth/register` | Công khai | Body: `username` (3–50 ký tự), `password` (6–255 ký tự), `name` (1–100 ký tự), `phone?` (tối đa 20 ký tự) | `201`: thông tin tài khoản, vai trò mặc định `customer`; không trả mật khẩu | `400`: trùng tên đăng nhập |
| Đăng nhập | `POST /api/auth/login` | Công khai | Body: `username`, `password` | `200`: `access_token`, `token_type`, `user` | `400`: sai tên đăng nhập hoặc mật khẩu |
| Đăng xuất trình duyệt | `POST /api/auth/logout` | Công khai | Không | `204`: xóa cookie trang suất chiếu; phía trình duyệt xóa token và user trong localStorage; JWT đã cấp còn hợp lệ tới khi hết hạn | — |
| Thông tin tài khoản | `GET /api/auth/me` | Đăng nhập | Không | `200`: `id`, `username`, `name`, `phone`, `role`, `created_at` | — |
| Danh sách phim | `GET /api/movies` | Công khai | Không | `200`: danh sách phim | — |
| Chi tiết phim | `GET /api/movies/{movie_id}` | Công khai | Path: `movie_id` | `200`: `id`, `title`, `description`, `duration`, `release_date`, `poster_url`, `created_at` | `404`: không có phim |
| Tạo phim | `POST /api/movies/create` | Admin | Body: `title`, `duration` (phút), `release_date`, `description?`, `poster_url?` | `201`: phim vừa tạo | `400`: trùng tên và ngày phát hành |
| Cập nhật phim | `PATCH /api/movies/update/{movie_id}` | Admin | Path: `movie_id`; body: các trường cần đổi trong `title`, `description`, `duration`, `release_date`, `poster_url` | `200`: phim sau cập nhật | `404`: không có phim |
| Xóa phim | `DELETE /api/movies/delete/{movie_id}` | Admin | Path: `movie_id` | `204`: không có body | `404`: không có phim |
| Xem đánh giá | `GET /api/movies/{movie_id}/reviews` | Công khai | Path: `movie_id` | `200`: danh sách đánh giá, mới nhất trước | `404`: không có phim |
| Viết đánh giá | `POST /api/movies/{movie_id}/reviews` | Đăng nhập | Path: `movie_id`; body: `rating` (số nguyên 1–5), `comment?` | `201`: `id`, `user_id`, `movie_id`, `rating`, `comment`, `created_at` | `404`: không có phim |
| Xóa đánh giá | `DELETE /api/reviews/{review_id}` | Tác giả hoặc Admin | Path: `review_id` | `204`: không có body | `403`: không có quyền; `404`: không có đánh giá |
| Danh sách phòng | `GET /api/screens` | Công khai | Không | `200`: danh sách phòng gồm `id`, `name`, `total_seats` | — |
| Tạo phòng | `POST /api/screens` | Admin | Body: `name` (không rỗng), `total_seats` (số nguyên ≥ 1) | `200`: phòng vừa tạo | — |
| Xóa phòng | `DELETE /api/screens/{screen_id}` | Admin | Path: `screen_id` | `204`: không có body | `404`: không có phòng |
| Danh sách ghế trong phòng | `GET /api/screens/{screen_id}/seats` | Công khai | Path: `screen_id` | `200`: danh sách ghế; chưa kèm tình trạng đặt theo suất | `404`: không có phòng |
| Thêm ghế | `POST /api/screens/{screen_id}/seats` | Admin | Path: `screen_id`; body: `row_letter` (tối đa 1 ký tự), `seat_number` (số nguyên), `type` (`standard`, `vip`, `sweetbox`) | `200`: `id`, `screen_id`, `row_letter`, `seat_number`, `type` | `400`: phòng đủ ghế; `404`: không có phòng; `409`: trùng vị trí |
| Xóa ghế | `DELETE /api/seats/{seat_id}` | Admin | Path: `seat_id` | `204`: không có body | `404`: không có ghế |
| Tra cứu suất chiếu | `GET /api/showtimes` | Công khai | Query: `movie_id`, `date` | `200`: danh sách suất chiếu theo phim và ngày | `404`: không có suất phù hợp |
| Suất chiếu và tình trạng ghế | `GET /api/showtimes/{showtime_id}` | Công khai | Path: `showtime_id` | `200`: `showtime`, `available_seats` (mỗi phần tử gồm `seat`, `is_available`) | `404`: không có suất chiếu |
| Tạo suất chiếu | `POST /api/showtimes` | Admin | Body: `movie_id`, `screen_id`, `start_time`, `end_time`, `base_price` (số nguyên) | `201`: `id`, `base_price`, `start_time`, `end_time` | `400`: thời gian không hợp lệ; `404`: không có phim/phòng; `409`: trùng lịch trong phòng |
| Xóa suất chiếu | `DELETE /api/showtimes/{showtime_id}` | Admin | Path: `showtime_id` | `204`: không có body | `404`: không có suất chiếu |
| Danh sách đồ ăn | `GET /food` | Công khai | Không | `200`: danh sách đồ ăn, sắp xếp theo tên tăng dần | — |
| Tạo món | `POST /food` | Admin | Body: `name` (1–255 ký tự), `price` (decimal ≥ 0), `description?`, `image_url?` | `201`: `id`, `name`, `description`, `price`, `image_url`; giá trả về dạng chuỗi decimal | — |
| Xóa món | `DELETE /food/{food_id}` | Admin | Path: `food_id` | `204`: không có body | `404`: không có món |
| Tạo đơn đặt vé | `POST /orders` | Đăng nhập | Body: `showtime_id`, `seat_ids` (ít nhất 1 UUID), `items?` (mặc định `[]`; mỗi món gồm `food_id`, `quantity` ≥ 1, mặc định 1) | `201`: đơn gồm `id`, `user_id`, `status`, `total_amount`, `created_at`, `order_foods`, `tickets` | `400`: lặp ID ghế/món hoặc ghế sai phòng; `404`: không có suất/món; `409`: ghế đã đặt hoặc lỗi ràng buộc khi commit |
| Danh sách đơn | `GET /orders` | Đăng nhập | Không | `200`: đơn của mình, mới nhất trước; admin xem mọi đơn | — |
| Chi tiết đơn | `GET /orders/{order_id}` | Chủ đơn hoặc Admin | Path: `order_id` | `200`: đơn cùng chi tiết vé và đồ ăn | `404`: không có đơn hoặc không thuộc quyền xem |
| Xóa đơn | `DELETE /orders/{order_id}` | Chủ đơn hoặc Admin | Path: `order_id` | `204`: không có body nếu xóa thành công | `404`: không có đơn hoặc không thuộc quyền xóa; có thể `500` do ràng buộc database |
| Kiểm tra API | `GET /health` | Công khai | Không | `200`: `{"status":"ok"}`; không truy vấn kiểm tra database | — |
| Swagger UI | `GET /docs` | Công khai | Không | `200`: giao diện xem và thử API | — |
| ReDoc | `GET /redoc` | Công khai | Không | `200`: tài liệu API | — |
| OpenAPI | `GET /openapi.json` | Công khai | Không | `200`: đặc tả OpenAPI dạng JSON | — |

**Lỗi chung:** `401` khi thiếu token, token sai hoặc hết hạn; `403` khi thiếu quyền; `422` khi đầu vào sai schema. Lỗi nghiệp vụ có dạng `{"detail":"Thông báo lỗi"}`; lỗi `422` có `detail` là danh sách lỗi theo trường. Lỗi database chưa được xử lý có thể trả `500`, kể cả khi xóa dữ liệu còn liên kết.

**Lưu ý triển khai:** các API danh sách chưa phân trang; lọc ngày suất chiếu phụ thuộc múi giờ session PostgreSQL. Schema phim cho phép bỏ qua `description`, `poster_url`, nhưng model hiện không cho phép `null` ở hai cột này. Loại ghế trong bảng là các giá trị của model, schema request hiện chưa kiểm tra enum. API tạo suất chiếu chưa kiểm tra giá không âm hoặc độ dài suất so với thời lượng phim.

<a id="luu-y-don-hang"></a>

## Lưu ý nghiệp vụ đơn hàng

- Tạo đơn tính giá phía server: `base_price × số ghế + tổng (giá món × số lượng)`. Chưa có phụ thu theo loại ghế. Giá và tổng tiền dạng decimal được trả dưới dạng chuỗi JSON.
- Đơn và vé mới mặc định `pending`; chưa có thanh toán, xác nhận đã thanh toán hoặc thời hạn tự giải phóng ghế. Response vé gồm `id`, `order_id`, `showtime_id`, `seat_id`, `price`; hiện không trả `status` của vé.
- API tạo đơn kiểm tra vé `pending`/`confirmed`, nhưng API tra cứu ghế coi mọi bản ghi vé là đã đặt. Unique `(showtime_id, seat_id)` trong model cũng áp dụng cho mọi trạng thái. Cần thống nhất quy tắc nếu bổ sung trạng thái hủy sau này.
- Đơn, vé và đồ ăn được commit cùng giao dịch. API bắt mọi `IntegrityError` khi commit và trả `409` với thông báo ghế bị đặt; không phải mọi lỗi ràng buộc đều thực sự do trùng ghế.
- Constraint trong model phải tồn tại trong database thực tế để chống ghi trùng. `create_all()` không thêm constraint mới vào bảng đã tồn tại; cần kiểm tra schema và kiểm thử nhiều yêu cầu đặt cùng ghế.
- API xóa đơn gọi `db.delete(order)` rồi commit. Quan hệ `Orders.tickets` dùng `passive_deletes=True`, trong khi khóa ngoại `Ticket.order_id` trong model chưa khai báo `ON DELETE CASCADE`. Nếu collection vé chưa được tải và database không có cascade tương ứng, xóa đơn có vé có thể thất bại. Vì vậy chưa khẳng định API đã hủy đơn và nhả ghế thành công trên database đang dùng. Đây cũng chưa phải cơ chế hủy có lưu lịch sử/hoàn tiền.
