from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def widthratio(value, arg):
    try:
        return float(value) / float(arg) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def get_alert_url(supply_type, alert_type):
    """Generate URL for alert cards based on type"""
    if alert_type == 'low_stock':
        return '?stock_status=low'
    elif alert_type == 'expiring':
        return '?expiration=expiring-soon'
    elif alert_type == 'expired':
        return '?expiration=expired'
    elif alert_type == 'out_of_stock':
        return '?stock_status=out'
    return '#'
