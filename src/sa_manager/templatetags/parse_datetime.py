from dateutil import parser
from django import template

register = template.Library()

@register.filter
def parse_datetime(s):
    return parser.parse(s)
