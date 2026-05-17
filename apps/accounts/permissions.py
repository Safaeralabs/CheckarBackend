from rest_framework.permissions import BasePermission


class HasRole(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in self.allowed_roles)


class IsAdminUserRole(HasRole):
    allowed_roles = ("admin",)


class IsOperatorOrAbove(HasRole):
    allowed_roles = ("operator", "inspector", "supervisor", "admin")


class IsInspectorOrAbove(HasRole):
    allowed_roles = ("inspector", "supervisor", "admin")


class IsSupervisorOrAbove(HasRole):
    allowed_roles = ("supervisor", "admin")
