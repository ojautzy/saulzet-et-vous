"""Access decorators for the dashboard app."""

from functools import wraps
from typing import Any

from django.contrib.auth.decorators import login_required
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
