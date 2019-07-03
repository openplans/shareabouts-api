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
    def tearDown(self):
        User.objects.all().delete()

    def test_GET_redirects_to_current_user(self):
        User.objects.create_user(username='mjumbewu', password='abc123')
        self.client.login(username='mjumbewu', password='abc123')

        response = self.client.get('/api/v2/users/current?param=value')

        self.assertStatusCode(response, 302, 303)
        self.assertEqual(response['Location'], '/api/v2/mjumbewu?param=value')

    def test_POST_authenticates_user(self):
        User.objects.create_user(username='mjumbewu', password='abc123')

        response = self.client.post('/api/v2/users/current', data={'username': 'mjumbewu', 'password': 'abc123'})

        self.assertStatusCode(response, 302, 303)
        self.assertEqual(response['Location'], 'http://testserver/api/v2/mjumbewu')

    def test_POST_requires_password(self):
        response = self.client.post('/api/v2/users/current', data={'username': 'mjumbewu'})

        self.assertStatusCode(response, 400)
        self.assertIn('errors', response.data)
        self.assertIn('password', response.data['errors'])

    def test_POST_requires_username(self):
        response = self.client.post('/api/v2/users/current', data={'password': 'abc123'})

        self.assertStatusCode(response, 400)
        self.assertIn('errors', response.data)
        self.assertIn('username', response.data['errors'])

    def test_POST_rejects_invalid_login(self):
        User.objects.create_user(username='mjumbewu', password='abc123')

        response = self.client.post('/api/v2/users/current', data={'username': 'mjumbewu', 'password': 'abc124'})

        self.assertStatusCode(response, 401)
        self.assertIn('errors', response.data)
        self.assertIn('__all__', response.data['errors'])

    def test_OPTIONS_is_allowed(self):
        User.objects.create_user(username='mjumbewu', password='abc123')

        response = self.client.options('/api/v2/users/current', data={'username': 'mjumbewu', 'password': 'abc123'})

        self.assertStatusCode(response, 200)

    def test_preflight_OPTIONS_is_allowed(self):
        User.objects.create_user(username='mjumbewu', password='abc123')

        response = self.client.options('/api/v2/users/current', data={'username': 'mjumbewu', 'password': 'abc123'}, HTTP_ORIGIN='http://www.example.com')

        self.assertStatusCode(response, 200)
        self.assertEqual(response['Access-Control-Allow-Origin'], 'http://www.example.com')
        self.assertEqual(response['Access-Control-Allow-Methods'], 'GET, POST, DELETE, HEAD, OPTIONS')


class UserInstanceViewTests (APITestMixin, TestCase):
    def tearDown(self):
        User.objects.all().delete()

    def test_GET(self):
        User.objects.create_user(username='mjumbewu', password='abc123')
        self.client.login(username='mjumbewu', password='abc123')

        response = self.client.get('/api/v2/mjumbewu')

        self.assertStatusCode(response, 200)

    def test_OPTIONS_is_allowed(self):
        User.objects.create_user(username='mjumbewu', password='abc123')

        response = self.client.options('/api/v2/mjumbewu')

        self.assertStatusCode(response, 200)

    def test_preflight_OPTIONS_is_allowed(self):
        User.objects.create_user(username='mjumbewu', password='abc123')

        response = self.client.options('/api/v2/mjumbewu', HTTP_ORIGIN='http://www.example.com')

        self.assertStatusCode(response, 200)
        self.assertEqual(response['Access-Control-Allow-Origin'], 'http://www.example.com')
        self.assertEqual(response['Access-Control-Allow-Methods'], 'GET, HEAD, OPTIONS')
