from django import template
from copy import name

register = template.Library()

@register.filter(name='split')
def split(value, key):
  return value.split(key)

@register.filter(name='zip')
def zip_lists(a, b):
  return zip(a, b)

@register.filter(name='zips')
def zip_lists(a, b,c):
  return zip(a, b,c)

@register.filter(name='list_iter')
def list_iter(lists):
    list_a, list_b, list_c = lists

    for x, y, z in zip(list_a, list_b, list_c):
        yield (x, y, z)
