"""Middleware for accounts app."""

import re
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

# URLs that unapproved users can access
EXEMPT_URL_PATTERNS = [
    re.compile(r"^/accounts/pending/$"),
    re.compile(r"^/accounts/logout/$"),
    re.compile(r"^/accounts/login/"),
    re.compile(r"^/accounts/register/$"),
    re.compile(r"^/accounts/magic/"),
    re.compile(r"^/admin/"),
    re.compile(r"^/static/"),
    re.compile(r"^/media/"),
    re.compile(r"^/$"),
]


class ApprovalMiddleware:
    """Redirect authenticated but unapproved users to the pending page."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if (
            request.user.is_authenticated
            and not request.user.is_approved
            and not request.user.is_superuser
            and not self._is_exempt(request.path)
        ):
            return redirect("accounts:pending")

        return self.get_response(request)

    def _is_exempt(self, path: str) -> bool:
        """Check if the path is exempt from approval check."""
        return any(pattern.match(path) for pattern in EXEMPT_URL_PATTERNS)
