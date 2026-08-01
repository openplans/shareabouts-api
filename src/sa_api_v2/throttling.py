from rest_framework.throttling import SimpleRateThrottle


class AnonymousIPThrottle(SimpleRateThrottle):
    """
    Limits the rate of requests from anonymous IP addresses.

    Requests that have an authenticated user OR a recognized client authentication
    (such as an API key or CORS origin) will bypass this throttle.
    """
    scope = 'anon_ip'

    def allow_request(self, request, view):
        # Skip throttling for authenticated users
        if getattr(request, 'user', None) and request.user.is_authenticated:
            return True

        # Skip throttling for client-authenticated requests (API Key or CORS Origin)
        if getattr(request, 'client', None) is not None:
            return True

        return super(AnonymousIPThrottle, self).allow_request(request, view)

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        if not ident:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
