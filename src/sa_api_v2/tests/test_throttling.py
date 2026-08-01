from unittest.mock import Mock
from django.test import TestCase
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from sa_api_v2.throttling import AnonymousIPThrottle


class DummyThrottledView(APIView):
    throttle_classes = [AnonymousIPThrottle]

    def get(self, request, *args, **kwargs):
        return Response({'status': 'ok'})


class AnonymousIPThrottleUnitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.throttle = AnonymousIPThrottle()
        # Rate limit is set to 2/min
        self.throttle.rate = '2/min'
        self.throttle.num_requests, self.throttle.duration = self.throttle.parse_rate(self.throttle.rate)

    def tearDown(self):
        cache.clear()

    def test_allow_request_for_authenticated_user(self):
        request = Mock()
        request.user.is_authenticated = True
        request.client = None

        self.assertTrue(self.throttle.allow_request(request, None))
        self.assertTrue(self.throttle.allow_request(request, None))
        # Third request should also be allowed for authenticated users
        self.assertTrue(self.throttle.allow_request(request, None))

    def test_allow_request_for_client_authenticated_request(self):
        request = Mock()
        request.user.is_authenticated = False
        request.client = Mock()  # API Key or CORS origin present

        self.assertTrue(self.throttle.allow_request(request, None))
        self.assertTrue(self.throttle.allow_request(request, None))
        # Third request should also be allowed for client-authenticated requests
        self.assertTrue(self.throttle.allow_request(request, None))

    def test_allow_request_throttling_for_fully_anonymous_request(self):
        request = Mock()
        request.user.is_authenticated = False
        request.client = None
        request.META = {'REMOTE_ADDR': '192.168.1.1'}

        self.assertTrue(self.throttle.allow_request(request, None))
        self.assertTrue(self.throttle.allow_request(request, None))
        # Third request exceeds limit for fully anonymous requests and should be throttled
        self.assertFalse(self.throttle.allow_request(request, None))

    def test_get_cache_key(self):
        request = Mock()
        request.META = {'REMOTE_ADDR': '192.168.1.1'}
        key = self.throttle.get_cache_key(request, None)
        self.assertEqual(key, 'throttle_anon_ip_192.168.1.1')


class AnonymousIPThrottleIntegrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()
        self.view = DummyThrottledView.as_view()

    def tearDown(self):
        cache.clear()

    def test_api_view_throttles_anonymous_requests(self):
        # AnonymousIPThrottle rate is 20/min in settings
        request = self.factory.get('/api/v2/test', REMOTE_ADDR='10.0.0.1')
        for _ in range(20):
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

        # 21st request from same IP gets throttled (429)
        response = self.view(request)
        self.assertEqual(response.status_code, 429)

    def test_api_view_does_not_throttle_authenticated_user(self):
        # Authenticated user requests
        for _ in range(25):
            request = self.factory.get('/api/v2/test', REMOTE_ADDR='10.0.0.2')
            request.user = Mock()
            request.user.is_authenticated = True
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_api_view_does_not_throttle_client_authenticated_request(self):
        # Client-authenticated requests (API key / CORS origin)
        for _ in range(25):
            request = self.factory.get('/api/v2/test', REMOTE_ADDR='10.0.0.3')
            request.user = Mock()
            request.user.is_authenticated = False
            request.client = Mock()
            response = self.view(request)
            self.assertEqual(response.status_code, 200)
