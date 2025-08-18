from django import template

register = template.Library()

@register.filter
def divisibleby(value, arg):
    return value // arg

@register.filter
def modulo(value, arg):
    return value % arg

@register.filter
def get_item(dictionary, key):
    """Returns an item from a dictionary by key"""
    if isinstance(key, int):
        # Handle numeric indices for lists
        try:
            return dictionary[key]
        except (IndexError, TypeError):
            return None
    # Handle dictionary keys
    return dictionary.get(key)

@register.filter
def get_range(value):
    """Returns a range of numbers from 0 to value-1"""
    return range(value)

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def get_item(dictionary, key):
    return dictionary.get(int(key), 0)

@register.filter
def floornum(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    return float(value) * float(arg)

@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def filter_status(queryset, status):
    return queryset.filter(status=status)

@register.filter
def filter_active(queryset, is_active):
    return queryset.filter(is_active=is_active)

@register.filter
def filter_upcoming(queryset):
    from django.utils import timezone
    return queryset.filter(start_date__gt=timezone.now().date())
