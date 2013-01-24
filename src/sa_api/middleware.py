import time
import logging

class RequestTimeLogger (object):
    def process_request(self, request):
        self.start_time = time.time()

    def process_response(self, request, response):
        duration = time.time() - self.start_time

        # Log the time information; the colums are:
        # - full path, duration, response status
        logger = logging.getLogger('request_timer')
        logger.info('Time for %s\t%s\t%s' % (
            request.get_full_path(),
            duration,
            response.status_code
        ))

        return response
