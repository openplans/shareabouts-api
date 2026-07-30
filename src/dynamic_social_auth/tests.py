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


class PipelineTests (TestCase):

    def test_get_username_prefixes_backend_name(self):
        from unittest.mock import MagicMock
        from dynamic_social_auth.pipeline import get_username

        backend = MagicMock()
        backend.name = 'citysso'
        backend.setting.return_value = ['username']

        strategy = MagicMock()
        strategy.setting.return_value = False
        strategy.storage.user.username_max_length.return_value = 150
        strategy.storage.user.clean_username.side_effect = lambda u: u
        strategy.storage.user.user_exists.return_value = False

        details = {'username': 'johndoe'}
        result = get_username(strategy, details, backend)
        self.assertEqual(result, {'username': 'citysso:johndoe'})

    def test_get_username_fallback_to_email(self):
        from unittest.mock import MagicMock
        from dynamic_social_auth.pipeline import get_username

        backend = MagicMock()
        backend.name = 'citysso'
        backend.setting.return_value = ['username']

        strategy = MagicMock()
        strategy.setting.return_value = False
        strategy.storage.user.username_max_length.return_value = 150
        strategy.storage.user.clean_username.side_effect = lambda u: u
        strategy.storage.user.user_exists.return_value = False

        details = {'email': 'johndoe@example.com'}
        result = get_username(strategy, details, backend)
        self.assertEqual(result, {'username': 'citysso:johndoe'})


class MigrationTests (TestCase):

    def test_update_and_reverse_usernames(self):
        from django.apps import apps
        from social_django.models import UserSocialAuth
        from sa_api_v2.models import User
        import importlib
        migration_0007 = importlib.import_module('dynamic_social_auth.migrations.0007_update_social_usernames')
        update_usernames = migration_0007.update_usernames
        reverse_usernames = migration_0007.reverse_usernames

        user1 = User.objects.create(username='alice')
        UserSocialAuth.objects.create(user=user1, provider='citysso', uid='101')

        user2 = User.objects.create(username='bob')
        UserSocialAuth.objects.create(user=user2, provider='twitter', uid='202')

        update_usernames(apps, None)

        user1.refresh_from_db()
        user2.refresh_from_db()
        self.assertEqual(user1.username, 'citysso:alice')
        self.assertEqual(user2.username, 'twitter:bob')

        reverse_usernames(apps, None)

        user1.refresh_from_db()
        user2.refresh_from_db()
        self.assertEqual(user1.username, 'alice')
        self.assertEqual(user2.username, 'bob')


