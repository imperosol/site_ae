from django import template

register = template.Library()


@register.filter
def cent_to_euro(value):
    return f"{value / 100:.2f} €"
