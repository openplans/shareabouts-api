import time
import logging
from django.utils.deprecation import MiddlewareMixin

class RequestTimeLogger (MiddlewareMixin):
    def process_request(self, request):
        self.start_time = time.time()

    def process_response(self, request, response):
        # NOTE: If there was some exception, or some other reason that the
        # process_request method was not called, we won't know the start time.
        # Check that we know it first.
        if hasattr(self, 'start_time'):
            duration = time.time() - self.start_time

            # Log the time information
            logger = logging.getLogger('utils.request_timer')
            logger.debug('(%0.3f) "%s %s" %s' % (
                duration,
                request.method,
                request.get_full_path(),
                response.status_code
            ))

        return response


class CookiesLogger (MiddlewareMixin):
    """
    Logs in the request and response.
    """
    def process_response(self, request, response):
        logger = logging.getLogger('utils.cookies_logger')
        logger.debug(
            '(%s)\n'
            '\n'
            'Request cookies: %s\n'
            '\n'
            'Response cookies: %s' % (
                response.status_code,
                request.COOKIES,
                response.cookies or {}
        ))
        return response


class JSEnableAllCookies (MiddlewareMixin):
    """
    Removes the httponly flag from all the cookies being set.
    """
    def process_response(self, request, response):
        if response.cookies:
            for morsel in list(response.cookies.values()):
                morsel['httponly'] = ''

        return response


class UniversalP3PHeader (MiddlewareMixin):
    """
    Sets P3P headers on the response. This header does not specify
    a valid P3P policy, but it is enough to get past IE.

    See http://stackoverflow.com/a/17710503/123776
    """
    def process_response(self, request, response):
        response['P3P'] = 'CP="Shareabouts does not have a P3P policy."'
        return response