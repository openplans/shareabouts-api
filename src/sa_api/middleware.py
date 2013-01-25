import time
import logging

class RequestTimeLogger (object):
    def process_request(self, request):
        self.start_time = time.time()

    def process_response(self, request, response):
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
