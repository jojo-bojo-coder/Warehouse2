from django import template
from django.contrib.auth.models import User
from club_dashboard.decorators import has_permission

register = template.Library()

@register.filter(name='has_club_permission')
def has_club_permission(user, permission_code):
    return has_permission(user, permission_code)