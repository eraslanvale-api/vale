from rest_framework import permissions

class IsManager(permissions.BasePermission):
    """
    Sadece 'Yönetici' rolüne sahip olanlara veya is_staff olanlara izin verir.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == 'Yönetici' or request.user.is_staff)
        )
