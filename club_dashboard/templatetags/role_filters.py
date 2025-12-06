from django import template

register = template.Library()

@register.filter
def get_permissions_display_in_language(role, language_code):
    return role.get_permissions_display(language_code)

@register.filter
def get_role_name_in_language(role, language_code):
    return role.get_name(language_code)

@register.filter
def get_role_name_in_language(role, language_code):
    """Get role name in specified language"""
    if hasattr(role, 'get_name'):
        return role.get_name(language_code)
    # Fallback for old roles that don't have bilingual support
    return getattr(role, 'name', str(role))