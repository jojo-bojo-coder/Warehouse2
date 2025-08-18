from django.core.exceptions import PermissionDenied
from functools import wraps

def has_permission(user, permission_code):
    """
    Helper function to check permissions that can be used in views and templates
    """
    # Skip permission check for superusers
    if user.is_superuser:
        return True

    # Get user's profile
    try:
        user_profile = user.userprofile

        # Allow directors and administrators by default
        if user_profile.director_profile or user_profile.administrator_profile or user_profile.vendor_manager_profile:
            return True

        # Check custom permissions for other roles
        if hasattr(user_profile, 'custom_role'):
            role = user_profile.custom_role
            if role.has_permission(permission_code):
                return True

    except AttributeError:
        pass

    return False

def club_permission_required(permission_code):
    """
    Decorator to check if user has permission to access a view.
    Allows directors and administrators by default.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if has_permission(request.user, permission_code):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator