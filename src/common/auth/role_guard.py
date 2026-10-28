"""
Role Guard — Authorization, chạy SAU Auth Middleware (get_current_user).

Auth Middleware (middleware.py) chỉ trả lời "user này là ai" (authentication).
Role Guard trả lời tiếp "user này có được phép gọi endpoint này không"
(authorization) — dựa trên field `role` trong CurrentUser.

Cách dùng ở B / C:

    from fastapi import Depends
    from common.role_guard import require_role

    # Chỉ admin mới được tạo showtime
    @router.post("/showtimes")
    def create_showtime(current_user = Depends(require_role("admin"))):
        ...

    # Cho phép nhiều role
    @router.get("/orders/{order_id}")
    def get_order(current_user = Depends(require_role("admin", "customer"))):
        ...
"""

from fastapi import Depends, HTTPException, status

from .middleware import get_current_user, get_page_user, CurrentUser

__all__ = ["require_role"]


def require_role(*allowed_roles: str, allow_cookie: bool = False):
    """
    Factory tạo dependency kiểm tra role — gọi require_role("admin") ngay
    trong khai báo route, không cần viết if/else lặp lại trong từng handler.

    Set allow_cookie=True only for read-only HTML pages that need browser
    navigation. API endpoints keep the default Bearer-only authentication.

    Quy tắc trả lỗi (đã thống nhất trong daily meeting):
        - Chưa đăng nhập / token không hợp lệ -> 401 (get_current_user raise trước)
        - Đăng nhập rồi nhưng role không nằm trong allowed_roles -> 403
    """

    auth_dependency = get_page_user if allow_cookie else get_current_user

    def role_checker(current_user: CurrentUser = Depends(auth_dependency)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Yêu cầu quyền: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker
