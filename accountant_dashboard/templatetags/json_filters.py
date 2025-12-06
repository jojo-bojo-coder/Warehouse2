import json
from django.core.serializers import serialize
from django.db.models import QuerySet
from django.template import Library

register = Library()

@register.filter
def to_json(value):
    if isinstance(value, QuerySet):
        return serialize('json', value)
    elif hasattr(value, '__iter__') and not isinstance(value, (str, dict)):
        return json.dumps(list(value))
    else:
        return json.dumps(value)
