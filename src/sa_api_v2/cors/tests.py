#from django.core.exceptions import PermissionDenied
#import mock
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from nose.tools import assert_true, assert_false, assert_raises, assert_is_not_none, assert_equal
from sa_api_v2.cors.auth import OriginAuthentication
from sa_api_v2.cors.models import Origin
from sa_api_v2.models import DataSet, User


class TestOriginMatching (TestCase):
    def test_match_simple_domains(self):
        pattern = 'github.com'
        assert_true(Origin.match(pattern, 'https://github.com'))
        assert_false(Origin.match(pattern, 'ftp://github.com'))
        assert_false(Origin.match(pattern, 'http://openplans.github.com'))

    def test_match_subdomains_with_asterisk(self):
        pattern = '*.github.com'
        assert_false(Origin.match(pattern, 'https://github.com'))
        assert_true(Origin.match(pattern, 'http://openplans.github.com'))
        assert_false(Origin.match(pattern, 'http://openplansngithub.com'))

    def test_match_ports_with_asterisk(self):
        pattern = 'localhost:*'
        assert_false(Origin.match(pattern, 'https://github.com'))
        assert_true(Origin.match(pattern, 'http://localhost:8000'))

    def test_match_domains_with_scheme(self):
        pattern = 'http://github.com'
        assert_false(Origin.match(pattern, 'https://github.com'))
        assert_true(Origin.match(pattern, 'http://github.com'))

    def test_lone_asterisk_matches_everything(self):
        pattern = '*'
        assert_true(Origin.match(pattern, 'https://ishkabibble.com:443'))


class TestOriginClientAuth (TestCase):
    def setUp(self):
        Origin.objects.all().delete()
        DataSet.objects.all().delete()

        self.user = User.objects.create_user(username='user', password='password')
        self.dataset = DataSet.objects.create(owner=self.user, slug='dataset')
        self.permission1 = Origin.objects.create(pattern='github.com', dataset=self.dataset)
        self.permission2 = Origin.objects.create(pattern='localhost:*', dataset=self.dataset)

    def test_simple_origin_matching_on_first_origin(self):
        checker = OriginAuthentication()
        client_auth = checker.check_origin_permission('http://github.com', self.dataset)

        assert_is_not_none(client_auth)
        assert_true(isinstance(client_auth, tuple))
        assert_equal(len(client_auth), 2)

    def test_simple_origin_matching_on_not_first_origin(self):
        checker = OriginAuthentication()
        client_auth = checker.check_origin_permission('http://localhost:8000', self.dataset)

        assert_is_not_none(client_auth)
        assert_true(isinstance(client_auth, tuple))
        assert_equal(len(client_auth), 2)

    def test_unknown_origin(self):
        checker = OriginAuthentication()
        with assert_raises(PermissionDenied):
            client_auth = checker.check_origin_permission('http://toyota.com', self.dataset)


#class TestApiKeyAuth(TestCase):

#    def _cleanup(self):
#        from .models import ApiKey
#        from django.contrib.auth.models import User
#        User.objects.all().delete()
#        ApiKey.objects.all().delete()

#    def setUp(self):
#        self._cleanup()

#    def tearDown(self):
#        self._cleanup()

#    def test_check_api_auth__no_credentials(self):
#        from .auth import check_api_authorization
#        from .auth import ApiKeyAuthentication
#        ip = '1.2.3.4'
#        request = mock.Mock(**{'user.is_authenticated.return_value': False,
#                               'user.is_active': True,
#                               'META': {'REMOTE_ADDR': ip},
#                               'GET': {}, 'POST': {}})
#        # Starts logged out...
#        self.assertEqual(request.user.is_authenticated(), False)
#        self.assertRaises(PermissionDenied, check_api_authorization,
#                          request)
#        self.assertEqual(None, ApiKeyAuthentication(None).authenticate(request))
#        # Still logged out.
#        self.assertEqual(request.user.is_authenticated(), False)

#    def test_check_api_auth__logged_in(self):
#        from .auth import check_api_authorization
#        from .auth import ApiKeyAuthentication
#        ip = '1.2.3.4'
#        request = mock.Mock(**{'user.is_authenticated.return_value': True,
#                               'user.is_active': True,
#                               'META': {'REMOTE_ADDR': ip},
#                               'GET': {}, 'POST': {}})
#        # Starts logged in...
#        self.assertEqual(request.user.is_authenticated(), True)
#        self.assertEqual(True, check_api_authorization(request))
#        self.assertEqual(request.user,
#                         ApiKeyAuthentication(None).authenticate(request))
#        # And still logged in.
#        self.assertEqual(request.user.is_authenticated(), True)

#    def test_check_api_auth__logged_in_but_disabled(self):
#        from .auth import check_api_authorization
#        from .auth import ApiKeyAuthentication
#        from django.core.exceptions import PermissionDenied
#        ip = '1.2.3.4'
#        get_request = mock.Mock(**{'user.is_authenticated.return_value': True,
#                                   'user.is_active': False,
#                                   'META': {'REMOTE_ADDR': ip},
#                                   'GET': {}, 'POST': {}})
#        # User is logged in...
#        self.assertEqual(get_request.user.is_authenticated(), True)
#        # ... but still denied.
#        self.assertRaises(PermissionDenied, check_api_authorization,
#                          get_request)
#        self.assertEqual(None,
#                         ApiKeyAuthentication(None).authenticate(get_request))
#        # Still logged in.
#        self.assertEqual(get_request.user.is_authenticated(), True)

#    def test_check_api_auth__key_invalid(self):
#        from .auth import check_api_authorization, KEY_HEADER
#        from .auth import ApiKeyAuthentication
#        from django.core.exceptions import PermissionDenied
#        key = '12345'
#        ip = '1.2.3.4'
#        get_request = mock.Mock(**{'user.is_authenticated.return_value': False,
#                                   'user.is_active': True,
#                                   'META': {'REMOTE_ADDR': ip,
#                                            KEY_HEADER: key},
#                                   'GET': {}, 'POST': {}})
#        # Starts logged out...
#        self.assertEqual(get_request.user.is_authenticated(), False)
#        self.assertRaises(PermissionDenied, check_api_authorization,
#                          get_request)
#        self.assertEqual(None,
#                         ApiKeyAuthentication(None).authenticate(get_request))
#        # Still logged out.
#        self.assertEqual(get_request.user.is_authenticated(), False)

#    def test_check_api_auth__key(self):
#        from .auth import check_api_authorization, KEY_HEADER
#        from .auth import ApiKeyAuthentication
#        from .models import generate_unique_api_key
#        from .models import ApiKey
#        from django.contrib.auth.models import User
#        ip = '1.2.3.4'
#        user = User.objects.create(username='bob@bob.com')
#        key = ApiKey.objects.create(key=generate_unique_api_key(), user=user)
#        get_request = mock.Mock(**{'user.is_authenticated.return_value': False,
#                                   'user.is_active': True,
#                                   'META': {'REMOTE_ADDR': ip,
#                                            KEY_HEADER: key},
#                                   'session': mock.MagicMock(),
#                                   'GET': {}, 'POST': {}})

#        # Starts logged out...
#        self.assertEqual(get_request.user.is_authenticated(), False)
#        self.assertEqual(True, check_api_authorization(get_request))
#        self.assertEqual(get_request.user,
#                         ApiKeyAuthentication(None).authenticate(get_request))
#        # And now logged in.
#        self.assertEqual(get_request.user.is_authenticated(), True)

#    def test_check_api_auth__key__with_disabled_user(self):
#        from .auth import check_api_authorization, KEY_HEADER
#        from .auth import ApiKeyAuthentication
#        from django.core.exceptions import PermissionDenied
#        ip = '1.2.3.4'
#        from .models import generate_unique_api_key
#        from .models import ApiKey
#        from django.contrib.auth.models import User
#        user = User.objects.create(username='bob@bob.com', is_active=False)
#        key = ApiKey.objects.create(key=generate_unique_api_key(), user=user)
#        get_request = mock.Mock(**{'user.is_authenticated.return_value': False,
#                                   'META': {'REMOTE_ADDR': ip,
#                                            KEY_HEADER: key},
#                                   'GET': {}, 'POST': {}})
#        # User is logged out...
#        self.assertEqual(get_request.user.is_authenticated(), False)
#        # ... and denied.
#        self.assertRaises(PermissionDenied, check_api_authorization,
#                          get_request)
#        self.assertEqual(None,
#                         ApiKeyAuthentication(None).authenticate(get_request))
#        # Still logged out.
#        self.assertEqual(get_request.user.is_authenticated(), False)
