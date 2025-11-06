"""Template tags"""

from django import template

from corphandouts.models import FittingCorrection

register = template.Library()


@register.filter
def correction_type(correction_type_value: str) -> str:
    """Filter to display a correction type correctly"""
    return FittingCorrection.CorrectionType.from_value_to_label(correction_type_value)
