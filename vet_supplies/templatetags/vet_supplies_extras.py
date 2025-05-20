from django import template

register = template.Library()

@register.simple_tag
def widthratio(value, max_value, max_width):
    try:
        return min((float(value) / float(max_value)) * max_width, 100)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
