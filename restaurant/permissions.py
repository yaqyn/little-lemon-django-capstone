from rest_framework.permissions import SAFE_METHODS, BasePermission


class StaffWriteOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_staff)


class PublicCreateStaffManage(BasePermission):
    def has_permission(self, request, view):
        return request.method == "POST" or bool(request.user and request.user.is_staff)
