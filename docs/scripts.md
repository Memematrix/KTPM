# Kịch bản trình bày dự án qua Google Meet

**Thời lượng đề xuất:** khoảng 6 phút, dành gần 1 phút dự phòng cho chuyển màn hình hoặc câu hỏi.

**Trọng tâm:** bài toán → nghiệp vụ → vấn đề cần xử lý → tổ chức mã nguồn → framework và yêu cầu kỹ thuật.

## Chuẩn bị trước buổi trình bày

- Mở sẵn [README](../README.md), Swagger Editor đã import [openapi.json](openapi.json) và thư mục [src](../src/).
- Phóng to chữ để thầy dễ đọc; tránh cuộn qua toàn bộ bảng API.
- Nếu nhóm có ba người: người 1 trình bày phần 1–2, người 2 phần 3–4, người 3 phần 5–6.
- Nên để một người điều khiển màn hình xuyên suốt.

## 1. Giới thiệu bài toán — 0:00 đến 0:40

**Màn hình:** README, phần “Bài toán và phạm vi”.

> Nhóm em xây dựng backend cho hệ thống quản lý rạp và đặt vé xem phim. Hệ thống phục vụ hai nhóm chính là khách hàng và quản trị viên.
>
> Bài toán cốt lõi là liên kết đúng phim, suất chiếu, phòng và ghế. Một ghế có thể được đặt ở nhiều suất khác nhau, nhưng không được đặt hai lần trong cùng một suất.
>
> Khách hàng có thể tra cứu, đặt vé kèm đồ ăn và quản lý đơn của mình. Quản trị viên quản lý dữ liệu rạp, lịch chiếu và các đơn hàng.

## 2. Mô tả nghiệp vụ chính — 0:40 đến 1:55

**Màn hình:** Swagger Editor, mở nhóm `orders` và endpoint `POST /orders`.

> Trước hết, quản trị viên thiết lập phim, phòng chiếu, ghế, suất chiếu và danh mục đồ ăn.
>
> Với khách hàng, luồng chính bắt đầu từ đăng nhập, chọn phim và ngày, chọn suất chiếu, xem ghế còn trống rồi gửi yêu cầu đặt vé.
>
> Trong API tạo đơn này, khách gửi mã suất chiếu, danh sách mã ghế và các món ăn kèm số lượng. Hệ thống kiểm tra suất chiếu tồn tại, ghế thuộc đúng phòng, các mã không bị lặp và ghế chưa được đặt.
>
> Tổng tiền được tính ở phía server bằng giá vé cơ bản nhân số ghế, cộng tiền đồ ăn. Sau đó hệ thống lưu đơn hàng, các bản ghi vé và chi tiết đồ ăn trong cùng một giao dịch.
>
> Khách chỉ được xem và xóa đơn của mình; quản trị viên được thao tác với mọi đơn. Phiên bản hiện tại chưa tích hợp thanh toán và giữ ghế có thời hạn, nên đơn mới ở trạng thái pending, chưa có nghĩa là đã thanh toán.

**Thao tác:** chỉ trỏ vào ví dụ request và response; không cần đọc tên từng trường.

## 3. Các vấn đề dễ thấy và hướng xử lý — 1:55 đến 3:15

**Màn hình:** README, phần “Các vấn đề cần xử lý và yêu cầu kỹ thuật”.

> Nhóm xác định ba vấn đề chính.
>
> Thứ nhất là đặt trùng ghế. Hai khách có thể cùng nhìn thấy ghế trống, nên chỉ kiểm tra trước khi đặt là chưa đủ. Model đã khai báo ràng buộc duy nhất theo cặp suất chiếu và ghế. Khi ghi dữ liệu vi phạm ràng buộc, API rollback giao dịch và trả lỗi. Nhóm vẫn cần xác nhận ràng buộc trên database thực tế và kiểm thử đồng thời để đánh giá đầy đủ.
>
> Thứ hai là tính hợp lệ của lịch chiếu và phòng. API đã kiểm tra thời gian kết thúc sau bắt đầu, không chồng lịch trong cùng phòng, ghế không trùng vị trí và không vượt sức chứa. Các trường hợp nhiều yêu cầu ghi cùng lúc vẫn cần kiểm tra thêm.
>
> Thứ ba là quyền truy cập. Hệ thống dùng JWT để xác thực, kiểm tra vai trò đối với API quản trị và kiểm tra quyền sở hữu đối với đơn hàng, đánh giá. Nhờ đó, người dùng không thể dùng mã đơn của người khác để xem chi tiết.

## 4. Kiến trúc và tổ chức mã nguồn — 3:15 đến 4:25

**Màn hình:** cây thư mục `src`; mở một router làm ví dụ.

> Hệ thống hiện được triển khai dưới dạng một ứng dụng FastAPI, chia thành các module chức năng và sử dụng chung PostgreSQL.
>
> File main khởi tạo ứng dụng và đăng ký các router. Thư mục common chứa cấu hình, kết nối database, xử lý JWT, băm mật khẩu và kiểm tra vai trò.
>
> Các chức năng được chia thành ba module: auth cho tài khoản cùng API phim và đánh giá; scheduling cho phòng, ghế, suất chiếu; ordering cho đồ ăn và đặt vé.
>
> Trong mỗi module, routers tiếp nhận và xử lý yêu cầu, schemas định nghĩa dữ liệu đầu vào/đầu ra, còn models ánh xạ bảng dữ liệu.
>
> Hiện nghiệp vụ và truy vấn database chủ yếu nằm trong router, chưa tách thành service và repository riêng. Khi nghiệp vụ mở rộng, nhóm dự kiến tách các phần này để dễ kiểm thử và giảm phụ thuộc.

## 5. Framework và yêu cầu kỹ thuật — 4:25 đến 5:20

**Màn hình:** README, danh sách công nghệ; chuyển sang Swagger Editor ở cuối phần.

> Nhóm sử dụng Python và FastAPI để xây dựng API. Pydantic kiểm tra cấu trúc dữ liệu đầu vào, đầu ra; SQLAlchemy Async và asyncpg phục vụ truy cập PostgreSQL bất đồng bộ.
>
> Tài khoản và JWT được ứng dụng tự quản lý; mật khẩu được băm bằng bcrypt. Supabase được dùng để cung cấp PostgreSQL, không dùng Supabase Auth cho luồng đăng nhập hiện tại.
>
> Các yêu cầu kỹ thuật nhóm tập trung là phân quyền đúng, dữ liệu nhất quán, ghi đơn cùng chi tiết trong một giao dịch và kiểm soát các trường hợp đặt trùng.
>
> Đặc tả API được lưu trong file OpenAPI JSON và có thể preview bằng Swagger Editor như trên màn hình. Tài liệu mô tả endpoint, dữ liệu gửi lên và cấu trúc phản hồi.

## 6. Tiến độ và phần cần hoàn thiện — 5:20 đến 6:00

**Màn hình:** README, phạm vi hiện tại.

> Hiện nhóm đã có các API quản lý rạp, tài khoản, đánh giá và tạo, tra cứu, xóa đơn hàng.
>
> Phần cần hoàn thiện tiếp theo là kiểm chứng đặt vé đồng thời, xử lý đầy đủ việc xóa đơn và giải phóng ghế, bổ sung migration database, sau đó triển khai giữ ghế có thời hạn và thanh toán.
>
> Nhóm cũng đã có báo cáo kiểm thử tải. Tuy nhiên, kết quả đó chỉ phản ánh kịch bản đã đo, chưa đủ để kết luận hệ thống xử lý tốt việc nhiều người cùng đặt một ghế.
>
> Nhóm em xin kết thúc phần trình bày và nhận góp ý của thầy.

## Câu hỏi dự kiến và gợi ý trả lời

### “Đã chống đặt trùng ghế chưa?”

> Code đã có unique constraint và rollback khi lỗi. Nhóm cần kiểm chứng constraint trên database đang dùng và chạy thử đồng thời trước khi khẳng định hoàn chỉnh.

### “Đặt vé đã có thanh toán chưa?”

> Chưa. Hiện API tạo đơn cùng bản ghi vé ở trạng thái pending; thanh toán là phần phát triển tiếp.

### “Đã phân tầng chưa?”

> Đã chia module, router, schema và model. Nghiệp vụ vẫn chủ yếu nằm trong router, chưa tách service/repository.

### “Xóa đơn có nhả ghế không?”

> Mục tiêu là xóa các vé liên quan để giải phóng ghế, nhưng cấu hình cascade hiện cần kiểm tra thêm. Nhóm chưa coi đây là luồng hủy đơn hoàn chỉnh.

## Lưu ý khi tập thử

Ưu tiên nói rõ một luồng đặt vé và vấn đề trùng ghế; không đọc lần lượt toàn bộ endpoint hoặc thư viện. Bấm giờ khi tập để điều chỉnh tốc độ nói và giữ phần trình bày trong 5–7 phút.
