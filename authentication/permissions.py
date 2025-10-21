from rest_framework.permissions import BasePermission
class PeopleCountPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_admin:
            return user.company
        if user.is_staff:
            return user.is_peoplecount
        return False