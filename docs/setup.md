# Hướng dẫn chạy dự án

[Quay lại README](../README.md).

## 1. Chuẩn bị

- Python **3.12+** hoặc công cụ **`uv`** để chạy trực tiếp (hỗ trợ cả **Linux/macOS** và **Windows**).
- PostgreSQL đang hoạt động hoặc một dự án Supabase có thông tin kết nối PostgreSQL.
- Docker và Docker Compose nếu chọn chạy bằng container.
- Mở terminal tại thư mục gốc repository, nơi chứa `pyproject.toml`, `requirements.txt` và `src/`.

## 2. Cấu hình môi trường

Nếu chưa có `.env`, sao chép file mẫu:

**Trên Linux / macOS (Bash):**
```bash
cp -n .env.example .env
```

**Trên Windows (PowerShell):**
```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Chỉnh các biến mà ứng dụng hiện sử dụng trong file `.env`:

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
SECRET_KEY=THAY_BANG_CHUOI_BI_MAT_NGAU_NHIEN
JWT_EXPIRE_MINUTES=60
```

- `DATABASE_URL`: URL PostgreSQL dùng driver `asyncpg`. Với Supabase, thay bằng thông tin kết nối của dự án và đúng cổng của loại kết nối được chọn; mẫu hiện có sử dụng pooler cổng `6543`.
- `SECRET_KEY`: khóa ký JWT.
- `JWT_EXPIRE_MINUTES`: thời hạn access token theo phút.
- JWT hiện được ký và kiểm tra bằng `HS256`. Dù settings có trường `algorithm`, mã JWT hiện dùng trực tiếp hằng số `HS256`

Có thể tạo khóa ngẫu nhiên bằng Python:

**Trên Linux / macOS:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Trên Windows:**
```powershell
py -3.12 -c "import secrets; print(secrets.token_hex(32))"
```

Dán kết quả vào `SECRET_KEY`. Nếu mật khẩu database có ký tự đặc biệt, cần mã hóa URL phần mật khẩu. Không đưa `.env` hoặc khóa thật vào Git.

## 3. Chạy trực tiếp với Python

### Cách 3.1: Dùng công cụ `uv` (Khuyên dùng - Nhanh và tự động quản lý môi trường)

Dự án đã có sẵn `pyproject.toml` và `uv.lock`. Sử dụng `uv` giúp bạn không cần cài đặt hoặc kích hoạt môi trường ảo thủ công:

1. **Cài đặt `uv` (nếu máy chưa có):**
   - **Linux / macOS:**
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     brew install uv (nếu có Homebrew)
     ```
   - **Windows:**
     ```powershell
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```

2. **Cài đặt dependencies và đồng bộ môi trường:**
   Tại thư mục gốc dự án:
   ```bash
   uv sync
   ```

3. **Khởi động API:**
   - Dùng lệnh `fastapi dev`:
     ```bash
     uv run fastapi dev src/main.py
     ```
   - Hoặc dùng trực tiếp `uvicorn`:
     ```bash
     uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
     ```

*(Nếu muốn kích hoạt môi trường ảo `.venv` do `uv` tạo ra: chạy `source .venv/bin/activate` trên Linux hoặc `.\.venv\Scripts\activate` trên Windows).*

---

### Cách 3.2: Dùng môi trường ảo chuẩn (`venv` và `pip`)

#### Trên Linux / macOS (Bash)

1. Tạo môi trường ảo và cài thư viện từ `requirements.txt`:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. Khởi động API từ thư mục gốc dự án:
   ```bash
   uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
   ```

*(Hoặc chạy trực tiếp qua binary trong `.venv` mà không cần kích hoạt môi trường:)*
```bash
./.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Trên Windows (PowerShell)

1. Tạo môi trường ảo và cài thư viện:
   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Khởi động API từ thư mục gốc dự án:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
   ```

> **Lưu ý khi khởi động:** Ứng dụng kết nối database và gọi `Base.metadata.create_all()` để tạo những bảng còn thiếu. Database cần tồn tại trước và tài khoản kết nối cần có quyền tạo bảng. Cơ chế này không tự cập nhật cấu trúc những bảng đã tồn tại; repo hiện chưa có cấu hình migration để chạy bằng Alembic.

## 4. Chạy bằng Docker Compose

Tạo và cấu hình `.env` như trên, sau đó chạy lệnh (áp dụng cho cả **Linux** và **Windows**):

```bash
docker compose up --build
```

Chạy nền, xem log hoặc dừng dịch vụ:

```bash
docker compose up --build -d
docker compose logs -f api
docker compose down
```

Compose hiện chỉ chạy dịch vụ API, ánh xạ cổng `8000` và mount mã nguồn để reload. PostgreSQL phải được cung cấp riêng. 
- Nếu kết nối tới Supabase Cloud: giữ nguyên `DATABASE_URL` trong `.env`.
- Nếu database chạy trên máy Windows host và API chạy bằng Docker Desktop: dùng `host.docker.internal` thay cho `localhost`.
- Nếu database chạy trên máy Linux host (ngoài container): dùng `172.17.0.1` (IP gateway mặc định của Docker) thay cho `localhost`.

## 5. Truy cập và thử API

- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)
- [OpenAPI JSON](http://localhost:8000/openapi.json)
- [Health check](http://localhost:8000/health)

Kiểm tra phản hồi của API:

**Trên Linux / macOS (Bash):**
```bash
curl -i http://localhost:8000/health
```

**Trên Windows (PowerShell):**
```powershell
Invoke-RestMethod -Uri 'http://localhost:8000/health'
```
