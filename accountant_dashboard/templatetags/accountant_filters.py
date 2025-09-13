from django import template
import json

register = template.Library()

@register.filter
def to_json(value):
    """Convert a Python object to JSON string"""
    return json.dumps(value)

@register.filter
def get_attr(obj, attr_name):
    """Get attribute from object"""
    try:
        return getattr(obj, attr_name)
    except AttributeError:
        return None

@register.filter
def map_attr(queryset, attr_name):
    """Extract a specific attribute from all objects in queryset"""
    return [getattr(obj, attr_name, None) for obj in queryset]

@register.tag(name='continue')
def do_continue(parser, token):
    return ContinueNode()

class ContinueNode(template.Node):
    def render(self, context):
        raise template.TemplateSyntaxError("Continue should be caught by for loop")



@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

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