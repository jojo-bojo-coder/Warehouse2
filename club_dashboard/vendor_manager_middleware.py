from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages


class VendorManagerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None

        if hasattr(request.user, 'userprofile') and request.user.userprofile.account_type == '8':
            # Vendor manager specific access control
            restricted_views = [
                'addDirector', 'editDirector', 'deleteDirector',  # Add other views to restrict
                # Add any other views that vendor managers shouldn't access
            ]

            if view_func.__name__ in restricted_views:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('club_dashboard_index')

            # Filter vendor-related views to only show vendors from their region
            if view_func.__name__ in ['viewVendors', 'vendorDetails']:
                # You'll need to modify these views to filter by region
                pass

        return None