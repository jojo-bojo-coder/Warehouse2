from coach_dashboard.models import CoachReceptionistTicket

def ticket_notifications(request):
    if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
        user_profile = request.user.userprofile
        if user_profile.account_type == '5':  # Receptionist
            unread_count = CoachReceptionistTicket.objects.filter(
                receptionist=user_profile.receptionist_profile,
                is_read=False
            ).count()
            return {'unread_ticket_count': unread_count}
    return {}