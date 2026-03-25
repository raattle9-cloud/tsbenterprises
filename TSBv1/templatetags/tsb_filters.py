"""Custom template filters for TSBv1."""
from django import template

register = template.Library()


@register.filter(name='as_float')
def as_float(value):
    """
    Convert MongoDB Decimal128 or any numeric type to a clean float string.
    Usage: {{ booking.remaining_amount|as_float }}
    """
    if value is None:
        return "0.00"
    try:
        # Try direct float conversion
        if isinstance(value, (int, float)):
            return f"{float(value):.2f}"
        # For Decimal128, Decimal, or other types — convert via string
        return f"{float(str(value)):.2f}"
    except (TypeError, ValueError):
        return "0.00"
