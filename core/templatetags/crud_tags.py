import builtins
from django import template

register = template.Library()


@register.filter
def getattr(obj, attr):
    try:
        return builtins.getattr(obj, attr, '')
    except (AttributeError, KeyError, TypeError):
        return ''


@register.filter
def verbose_name(obj):
    return obj._meta.verbose_name


@register.filter
def verbose_name_plural(obj):
    return obj._meta.verbose_name_plural


@register.filter
def dictkey(dct, key):
    try:
        return dct.get(key, '')
    except (AttributeError, TypeError):
        return ''
