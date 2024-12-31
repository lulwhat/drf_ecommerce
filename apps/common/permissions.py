from rest_framework import permissions


class IsOwnerOrStaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated or request.user.is_staff

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff


class IsSellerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return ((request.user.is_authenticated
                 and request.user.account_type == 'SELLER')
                or request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        return obj.seller == request.user.seller or request.user.is_staff


class IsOwnerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.user.id == request.user.id
