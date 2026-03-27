"""Access decorators for the dashboard app."""

from functools import wraps
from typing import Any

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden


def elected_required(view_func: Any) -> Any:
    """Restrict access to elected officials (elected + mayor roles).

    Combines login_required check with role verification.
    Returns 403 if the user is not an elected official.
    """

    @wraps(view_func)
    @login_required
    def _wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_elected:
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)

    return _wrapped


def mayor_required(view_func: Any) -> Any:
    """Restrict access to mayor and admin users."""

    @wraps(view_func)
    @login_required
    def _wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_mayor and not request.user.is_admin:
            return HttpResponseForbidden()
        return view_func(request, *args, **kwargs)

    return _wrapped


def admin_required(view_func: Any) -> Any:
    """Restrict access to admin users only."""

    @wraps(view_func)
    @login_required
    def _wrapped(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated or not request.user.is_admin:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped
