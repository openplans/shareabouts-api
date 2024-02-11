from django.test import TestCase, Client
from .models import OAuth2Provider


class DynamicAuthProviderTests (TestCase):

    def test_auth_uses_model(self):
        login_url = 'https://example.com/login'
        OAuth2Provider.objects.create(
            name='pingid',
            authorization_url=login_url,
            access_token_url='https://example.com/access-token',
        )

        client = Client()
        response = client.get('/api/v2/users/login/pingid/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'][:len(login_url)], login_url)

    def test_auth_respects_new_providers(self):
        """
        This test checks that new provider instances are checked for even after
        auth has been done once (i.e. that we're not caching the provider
        instances too aggressively).
        """
        # Create the first provider
        login_url1 = 'https://example1.com/login1'
        OAuth2Provider.objects.create(
            name='provider1',
            authorization_url=login_url1,
            access_token_url='https://example1.com/access-token',
        )

        client = Client()
        response = client.get('/api/v2/users/login/provider2/')
        self.assertEqual(response.status_code, 404)

        # Create the second provider
        login_url2 = 'https://example2.com/login2'
        OAuth2Provider.objects.create(
            name='provider2',
            authorization_url=login_url2,
            access_token_url='https://example2.com/access-token',
        )

        response = client.get('/api/v2/users/login/provider2/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'][:len(login_url2)], login_url2)


class DynamicClientRequestTests (TestCase):

    def test_client_id_secret_used(self):
        login_url = 'https://example1.com/login'
        OAuth2Provider.objects.create(
            name='provider',
            authorization_url=login_url,
            access_token_url='https://example.com/access-token',
        )

        client = Client()
        response = client.get('/api/v2/users/login/provider/?client_id=abc&client_secret=123')
        self.assertIn('client_id=abc', response.headers['Location'])
        self.assertNotIn('client_secret', response.headers['Location'])
