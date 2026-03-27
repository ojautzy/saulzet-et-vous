"""Template tags for the dashboard app."""

from django import template

from apps.reports.models import Report

register = template.Library()


@register.simple_tag(takes_context=True)
def assigned_count(context: dict) -> int:
    """Return the number of reports assigned to the current user."""
    request = context.get("request")
    if not request or not hasattr(request, "user") or not request.user.is_authenticated:
        return 0
    if not request.user.is_elected:
        return 0
    return Report.objects.filter(
        assigned_to=request.user,
        status__in=[Report.Status.ASSIGNED, Report.Status.IN_PROGRESS],
    ).count()


@register.filter
def dict_get(d, key):
    """Get a value from a dictionary by key."""
    if isinstance(d, dict):
        return d.get(key, 0)
    return 0
