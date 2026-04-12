"""Security middleware for saulzet_et_vous."""


class ContentSecurityPolicyMiddleware:
    """Add Content-Security-Policy header to all responses."""

    CSP_POLICY = "; ".join(
        [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com",
            "style-src 'self' 'unsafe-inline' https://unpkg.com",
            "img-src 'self' data: https://*.tile.openstreetmap.org",
            "font-src 'self'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
        ]
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = self.CSP_POLICY
        return response
