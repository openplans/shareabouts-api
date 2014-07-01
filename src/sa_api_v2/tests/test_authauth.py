from django.test import TestCase
from django.test.client import RequestFactory
from ..models import User
from ..views import CurrentUserInstanceView


class APITestMixin (object):
    def assertStatusCode(self, response, *expected):
        if hasattr(response, 'rendered_content'):
            content = response.rendered_content
        elif hasattr(response, 'content'):
            content = response.content
        elif response.status_code in (301, 302, 303):
            content = response.get('Location')

        self.assertIn(response.status_code, expected,
            'Status code not in %s response: (%s) %s' %
            (expected, response.status_code, content))


class CurrentUserViewTests (APITestMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def tearDown(self):
        User.objects.all().delete()

    def test_GET_redirects_to_current_user(self):
        User.objects.create_user(username='mjumbewu', password='abc123')
        self.client.login(username='mjumbewu', password='abc123')

        response = self.client.get('/api/v2/users/current?param=value')

        self.assertStatusCode(response, 303)
        self.assertEqual(response['Location'], 'http://testserver/api/v2/mjumbewu?param=value')

    def test_POST_authenticates_user(self):
        User.objects.create_user(username='mjumbewu', password='abc123')

        response = self.client.post('/api/v2/users/current', data={'username': 'mjumbewu', 'password': 'abc123'})

        self.assertStatusCode(response, 303)
        self.assertEqual(response['Location'], 'http://testserver/api/v2/mjumbewu')
