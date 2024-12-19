from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Allows read-only access for unauthenticated users.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

class IsAuthorOrReadOnly(BasePermission):
    """
    Allows authors to edit their own posts.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.post.author == request.user
