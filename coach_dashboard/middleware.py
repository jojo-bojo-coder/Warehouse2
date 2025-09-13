from django.shortcuts import redirect
from django.urls import reverse


class CoachPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Skip if not authenticated
        if not request.user.is_authenticated:
            return response

        # Skip if user doesn't have a userprofile
        if not hasattr(request.user, 'userprofile'):
            return response

        # Skip if user doesn't have a Coach_profile (not a coach)
        if not hasattr(request.user.userprofile, 'Coach_profile'):
            return response

        # Get the coach profile - add None check
        coach = getattr(request.user.userprofile, 'Coach_profile', None)
        if coach is None:
            return response

        # Skip for the upload policies page itself
        if request.path == reverse('upload_policies'):
            return response

        # Skip for static files and admin
        if request.path.startswith('/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response

        # Check if policies are approved - only for coaches
        if not coach.policies_approved:
            return redirect('upload_policies')

        return response