from django import template
from django.utils import timezone

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Retrieve a value from a dict by key. Works with int or str keys."""
    if isinstance(dictionary, dict):
        # Try both the key as-is and as int (for PKs)
        value = dictionary.get(key)
        if value is None:
            try:
                value = dictionary.get(int(key))
            except (TypeError, ValueError):
                pass
        return value if value is not None else []
    return []


@register.filter(name='floatformat_0')
def floatformat_0(value):
    """Return float formatted with 0 decimal places."""
    try:
        return f"{float(value):.0f}"
    except (TypeError, ValueError):
        return value


@register.filter(name='days_since')
def days_since(dt):
    """Return the number of days elapsed since a datetime."""
    if not dt:
        return 0
    now = timezone.now()
    if dt.tzinfo is None:
        from django.utils import timezone as tz
        dt = tz.make_aware(dt)
    delta = now - dt
    return delta.days
