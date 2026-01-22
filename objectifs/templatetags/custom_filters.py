from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Permet d'accéder aux éléments d'un dictionnaire dans les templates"""
    if dictionary is None:
        return None
    return dictionary.get(key)