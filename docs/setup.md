# Hướng dẫn chạy dự án

[Quay lại README](../README.md).

## 1. Chuẩn bị

- Python **3.12+** để chạy trực tiếp; các lệnh dưới đây sử dụng PowerShell trên Windows.
- PostgreSQL đang hoạt động hoặc một dự án Supabase có thông tin kết nối PostgreSQL.
- Docker và Docker Compose nếu chọn chạy bằng container.
- Mở terminal tại thư mục gốc repository, nơi chứa `requirements.txt` và `src/`.

## 2. Cấu hình môi trường

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
- `SECRET_KEY`: khóa ký JWT.
- `JWT_EXPIRE_MINUTES`: thời hạn access token theo phút.
- JWT hiện được ký và kiểm tra bằng `HS256`. Dù settings có trường `algorithm`, mã JWT hiện dùng trực tiếp hằng số `HS256`.
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET` trong file mẫu chưa được sử dụng bởi luồng API hiện tại; kết nối dữ liệu dùng `DATABASE_URL`.

Có thể tạo khóa ngẫu nhiên bằng Python:

```powershell
py -3.12 -c "import secrets; print(secrets.token_hex(32))"
```

Dán kết quả vào `SECRET_KEY`. Nếu mật khẩu database có ký tự đặc biệt, cần mã hóa URL phần mật khẩu. Không đưa `.env` hoặc khóa thật vào Git.

## 3. Chạy trực tiếp với Python

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

## 4. Chạy bằng Docker Compose

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

**Lưu ý phiên bản:** Dockerfile hiện dùng `python:3.11-slim`, trong khi dự án khai báo Python 3.12+. Để môi trường Docker thống nhất với dự án, đổi dòng `FROM` trong Dockerfile thành `FROM python:3.12-slim` trước khi build. Dockerfile trong repo hiện chưa được đồng bộ phiên bản.

## 5. Truy cập và thử API

- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)
- [OpenAPI JSON](http://localhost:8000/openapi.json)
- [Health check](http://localhost:8000/health)

Kiểm tra phản hồi của API bằng PowerShell:

```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/health'
```
