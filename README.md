# Hệ thống bán vé xem phim

Đồ án Kỹ thuật phần mềm xây dựng ứng dụng quản lý và bán vé xem phim. Hệ thống cung cấp API để quản lý tài khoản, danh mục phim, phòng chiếu, ghế, lịch chiếu, đánh giá và đồ ăn.

Phiên bản hiện tại tập trung vào backend. Trang chủ chỉ là giao diện mẫu; các chức năng được sử dụng và kiểm tra qua Swagger UI hoặc công cụ gọi HTTP API. Luồng đặt vé, tạo đơn hàng và thanh toán đang nằm trong định hướng phát triển, chưa có API triển khai.

## 1. Công nghệ sử dụng

- **Python 3.12 trở lên:** phiên bản khai báo trong `pyproject.toml` và `.python-version`.
- **FastAPI, Uvicorn:** xây dựng REST API và chạy máy chủ ứng dụng.
- **SQLAlchemy Async, asyncpg:** ánh xạ dữ liệu và truy cập PostgreSQL bất đồng bộ.
- **PostgreSQL / Supabase:** lưu trữ dữ liệu; cấu hình mẫu sử dụng PostgreSQL do Supabase cung cấp.
- **Pydantic, pydantic-settings:** khai báo request/response, kiểm tra dữ liệu và đọc cấu hình từ `.env`.
- **PyJWT, Passlib, bcrypt:** phát hành và xác thực JWT, băm mật khẩu, phân quyền truy cập.
- **Jinja2:** render trang HTML mẫu.
- **Docker, Docker Compose:** đóng gói và chạy dịch vụ API.

Ứng dụng tự quản lý tài khoản và JWT; luồng đăng nhập hiện tại không sử dụng Supabase Auth.

## 2. Luồng nghiệp vụ

### 2.1. Vai trò sử dụng

- **Khách chưa đăng nhập:** xem danh sách và chi tiết phim, đánh giá, phòng chiếu, sơ đồ ghế, suất chiếu và đồ ăn; đăng ký hoặc đăng nhập.
- **Khách hàng (`customer`):** có các quyền tra cứu trên, xem thông tin tài khoản, viết đánh giá và xóa đánh giá của mình.
- **Quản trị viên (`admin`):** quản lý phim, phòng chiếu, ghế, suất chiếu, đồ ăn và được xóa đánh giá của người dùng khác.

### 2.2. Đăng ký và đăng nhập

1. Người dùng gửi tên đăng nhập, mật khẩu, họ tên và số điện thoại nếu có.
2. Hệ thống kiểm tra tên đăng nhập đã tồn tại, băm mật khẩu và tạo tài khoản với vai trò mặc định `customer`.
3. Người dùng đăng nhập bằng tên đăng nhập và mật khẩu.
4. Hệ thống kiểm tra thông tin và trả về access token JWT cùng thông tin tài khoản.
5. Người dùng gửi token trong header `Authorization` để gọi các API yêu cầu đăng nhập. Hệ thống kiểm tra thêm vai trò đối với API quản trị.

### 2.3. Thiết lập dữ liệu rạp và lịch chiếu

1. Quản trị viên tạo phim với tên, mô tả, thời lượng, ngày phát hành và ảnh poster.
2. Quản trị viên tạo phòng chiếu và khai báo sức chứa.
3. Quản trị viên thêm từng ghế vào phòng, xác định hàng ghế, số ghế và loại ghế.
4. Quản trị viên tạo suất chiếu bằng cách chọn phim, phòng, thời gian bắt đầu, thời gian kết thúc và giá vé cơ bản.
5. Quản trị viên bổ sung danh mục đồ ăn với tên, giá, mô tả và hình ảnh.

Các ràng buộc đã có trong code:

- Không tạo phim trùng đồng thời tên và ngày phát hành theo phép kiểm tra hiện tại của API.
- Phòng chiếu có sức chứa ít nhất 1 ghế; số ghế được thêm không được vượt sức chứa.
- Ghế không được trùng hàng và số ghế trong cùng phòng. Ký hiệu hàng được chuyển thành chữ hoa khi tạo.
- Phim và phòng được chọn để tạo suất chiếu phải tồn tại.
- Thời gian kết thúc phải sau thời gian bắt đầu.
- Hai suất chiếu trong cùng phòng không được chồng lấn thời gian. Suất sau có thể bắt đầu đúng lúc suất trước kết thúc; hiện chưa tính khoảng nghỉ giữa hai suất.
- Giá đồ ăn không âm.

### 2.4. Tra cứu phim, suất chiếu và tình trạng ghế

1. Khách xem danh sách phim và chọn một phim để xem chi tiết.
2. Khách chọn ngày; hệ thống tra cứu suất chiếu theo `movie_id` và `date`.
3. Khách chọn suất chiếu; hệ thống trả về thông tin suất chiếu và danh sách ghế kèm `is_available`.
4. Ghế được xem là đã đặt nếu có bản ghi vé (`tickets`) gắn với ghế đó trong suất chiếu được chọn.

Hiện tại đã có model vé và API đọc tình trạng ghế, nhưng chưa có API tạo vé, giữ ghế hoặc hủy vé.

### 2.5. Đánh giá phim

1. Người dùng đã đăng nhập chọn phim và gửi điểm từ 1 đến 5, kèm bình luận nếu có.
2. Hệ thống kiểm tra phim tồn tại rồi lưu đánh giá theo tài khoản đang đăng nhập.
3. Mọi người có thể xem đánh giá của phim, sắp xếp từ mới đến cũ.
4. Chỉ tác giả đánh giá hoặc quản trị viên được xóa đánh giá đó.

API hiện chưa yêu cầu người dùng đã mua vé và chưa giới hạn mỗi tài khoản chỉ được đánh giá một lần cho một phim.

### 2.6. Luồng đặt vé dự kiến

Luồng dự kiến: chọn phim → chọn suất chiếu → chọn ghế → chọn đồ ăn → tạo đơn hàng → thanh toán → nhận vé.

Các bước từ chọn ghế để đặt mua đến nhận vé chưa được cung cấp thành API trong phiên bản hiện tại. Cơ chế giữ ghế, chống đặt trùng khi có nhiều yêu cầu đồng thời, thanh toán và hủy đơn cần được triển khai thêm.

## 3. Đặc tả API

Base URL: `http://localhost:8000`. Body dùng JSON; các ID là UUID, ngày dùng `YYYY-MM-DD`, ngày giờ dùng ISO 8601. Trường có dấu `?` là tùy chọn; các trường còn lại là bắt buộc, trừ body cập nhật phim.

API yêu cầu đăng nhập sử dụng header `Authorization: Bearer <access_token>`; quyền **Admin** tương ứng vai trò `admin`. Xem schema và thử request tại [Swagger UI](http://localhost:8000/docs).

| Chức năng | Method và endpoint | Quyền | Đầu vào | Thành công / Đầu ra | Lỗi nghiệp vụ |
| --- | --- | --- | --- | --- | --- |
| Đăng ký | `POST /api/auth/register` | Công khai | Body: `username` (3–50 ký tự), `password` (6–255 ký tự), `name` (1–100 ký tự), `phone?` (tối đa 20 ký tự) | `201`: thông tin tài khoản, vai trò mặc định `customer`; không trả mật khẩu | `400`: trùng tên đăng nhập |
| Đăng nhập | `POST /api/auth/login` | Công khai | Body: `username`, `password` | `200`: `access_token`, `token_type`, `user` | `400`: sai tên đăng nhập hoặc mật khẩu |
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
| Trang chủ | `GET /` | Công khai | Không | `200`: trang HTML mẫu | — |
| Kiểm tra API | `GET /health` | Công khai | Không | `200`: `{"status":"ok"}`; không truy vấn kiểm tra database | — |
| Swagger UI | `GET /docs` | Công khai | Không | `200`: giao diện xem và thử API | — |
| ReDoc | `GET /redoc` | Công khai | Không | `200`: tài liệu API | — |
| OpenAPI | `GET /openapi.json` | Công khai | Không | `200`: đặc tả OpenAPI dạng JSON | — |

**Lỗi chung:** `401` khi thiếu token, token sai hoặc hết hạn; `403` khi thiếu quyền; `422` khi đầu vào sai schema. Lỗi nghiệp vụ có dạng `{"detail":"Thông báo lỗi"}`; lỗi `422` có `detail` là danh sách lỗi theo trường. Lỗi database chưa được xử lý có thể trả `500`, kể cả khi xóa dữ liệu còn liên kết.

**Lưu ý triển khai:** các API danh sách chưa phân trang; lọc ngày suất chiếu phụ thuộc múi giờ session PostgreSQL. Schema phim cho phép bỏ qua `description`, `poster_url`, nhưng model hiện không cho phép `null` ở hai cột này. Loại ghế trong bảng là các giá trị của model, schema request hiện chưa kiểm tra enum. API tạo suất chiếu chưa kiểm tra giá không âm hoặc độ dài suất so với thời lượng phim.

## 4. Cách chạy dự án

### 4.1. Chuẩn bị

- Python **3.12+** để chạy trực tiếp; các lệnh dưới đây sử dụng PowerShell trên Windows.
- PostgreSQL đang hoạt động hoặc một dự án Supabase có thông tin kết nối PostgreSQL.
- Docker và Docker Compose nếu chọn chạy bằng container.
- Mở terminal tại thư mục gốc repository, nơi chứa `requirements.txt` và `src/`.

### 4.2. Cấu hình môi trường

Nếu chưa có `.env`, sao chép file mẫu bằng PowerShell:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Chỉnh các biến mà ứng dụng hiện sử dụng:

```dotenv
DATABASE_URL=postgresql+asyncpg://DB_USER:DB_PASSWORD@DB_HOST:5432/DB_NAME
SECRET_KEY=THAY_BANG_CHUOI_BI_MAT_NGAU_NHIEN
JWT_EXPIRE_MINUTES=60
```

- `DATABASE_URL`: URL PostgreSQL dùng driver `asyncpg`. Với Supabase, thay bằng thông tin kết nối của dự án và đúng cổng của loại kết nối được chọn; mẫu hiện có sử dụng pooler cổng `6543`.
- `SECRET_KEY`: khóa ký JWT. **File `.env.example` hiện ghi `JWT_SECRET_KEY`, nhưng code đọc `SECRET_KEY`; cần đổi tên biến này trong `.env`.**
- `JWT_EXPIRE_MINUTES`: thời hạn access token theo phút.
- JWT hiện được ký và kiểm tra bằng `HS256`. Dù settings có trường `algorithm`, mã JWT hiện dùng trực tiếp hằng số `HS256`.
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET` trong file mẫu chưa được sử dụng bởi luồng API hiện tại; kết nối dữ liệu dùng `DATABASE_URL`.

Có thể tạo khóa ngẫu nhiên bằng Python:

```powershell
py -3.12 -c "import secrets; print(secrets.token_hex(32))"
```

Dán kết quả vào `SECRET_KEY`. Nếu mật khẩu database có ký tự đặc biệt, cần mã hóa URL phần mật khẩu. Không đưa `.env` hoặc khóa thật vào Git.

### 4.3. Chạy trực tiếp với Python

Tạo môi trường ảo và cài thư viện:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Khởi động API từ thư mục gốc:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

Các lệnh gọi trực tiếp Python trong môi trường ảo nên không cần kích hoạt môi trường bằng `Activate.ps1`. Nếu dùng Linux/macOS, dùng `python3.12 -m venv .venv` và thay đường dẫn Python bằng `.venv/bin/python`.

Khi khởi động, ứng dụng kết nối database và gọi `Base.metadata.create_all()` để tạo những bảng còn thiếu. Database cần tồn tại trước và tài khoản kết nối cần có quyền tạo bảng. Cơ chế này không tự cập nhật cấu trúc những bảng đã tồn tại; repo hiện chưa có cấu hình migration để chạy bằng Alembic.

### 4.4. Chạy bằng Docker Compose

Tạo và cấu hình `.env` như trên, sau đó chạy:

```powershell
docker compose up --build
```

Chạy nền, xem log hoặc dừng dịch vụ:

```powershell
docker compose up --build -d
docker compose logs -f api
docker compose down
```

Compose hiện chỉ chạy dịch vụ API, ánh xạ cổng `8000` và mount mã nguồn để reload. PostgreSQL phải được cung cấp riêng. Nếu database chạy trên máy Windows host và API chạy bằng Docker Desktop, dùng `host.docker.internal` thay cho `localhost` trong `DATABASE_URL`.

**Lưu ý phiên bản:** Dockerfile hiện dùng `python:3.11-slim`, trong khi dự án khai báo Python 3.12+. Để môi trường Docker thống nhất với dự án, đổi dòng `FROM` trong Dockerfile thành `FROM python:3.12-slim` trước khi build. README này không thay đổi Dockerfile.

### 4.5. Truy cập và thử API

- [Trang chủ](http://localhost:8000/)
- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)
- [OpenAPI JSON](http://localhost:8000/openapi.json)
- [Health check](http://localhost:8000/health)

Kiểm tra phản hồi của API bằng PowerShell:

```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/health'
```

Quy trình thử trên Swagger UI:

1. Gọi `POST /api/auth/register` để tạo tài khoản.
2. Gọi `POST /api/auth/login`, sao chép `access_token` trong response.
3. Chọn **Authorize**, dán token vào ô HTTP Bearer rồi xác nhận.
4. Gọi `GET /api/auth/me` để kiểm tra đăng nhập.
5. Dùng tài khoản admin để tạo phim, phòng, ghế, suất chiếu và đồ ăn; sau đó thử các API tra cứu và đánh giá.

### 4.6. Chuẩn bị tài khoản quản trị để thử nghiệm

API đăng ký luôn tạo tài khoản `customer`; hiện chưa có API cấp quyền quản trị. Trong database phát triển, sau khi đăng ký một tài khoản riêng, có thể cấp quyền bằng SQL:

```sql
UPDATE users
SET role = 'admin'
WHERE username = 'admin_demo';
```

Thay `admin_demo` bằng tên tài khoản đã đăng ký. Đăng nhập lại sau khi đổi quyền để lấy token mới, vì vai trò được lưu trong JWT.

### 4.7. Các điểm cần kiểm tra khi không chạy được

- **Thiếu `secret_key`:** kiểm tra `.env` sử dụng `SECRET_KEY`, không phải `JWT_SECRET_KEY`.
- **Không kết nối được database:** kiểm tra host, cổng, tên database, tài khoản, mật khẩu và khả năng truy cập từ môi trường đang chạy API.
- **Không tìm thấy `src` hoặc template:** chạy lệnh từ thư mục gốc repository.
- **API quản trị trả `403`:** kiểm tra vai trò tài khoản và đăng nhập lại sau khi đổi quyền.
- **Database có cấu trúc cũ:** đối chiếu các model hiện tại; `create_all()` không thực hiện migration cho bảng sẵn có.

Tài liệu bổ sung trong repository: `database-schema.md` và `ke-hoach-du-an-ban-ve-phim.md`. Đây là tài liệu thiết kế/kế hoạch; phạm vi API đã triển khai được mô tả ở phần 3 và sinh tự động tại `/docs`.
