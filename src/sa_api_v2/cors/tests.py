from django.test import TestCase
from django.core.exceptions import PermissionDenied
from sa_api_v2.cors.auth import OriginAuthentication
from sa_api_v2.cors.models import Origin
from sa_api_v2.models import DataSet, User


class TestOriginMatching (TestCase):
    def test_match_simple_domains(self):
        pattern = 'github.com'
        self.assertTrue(Origin.match(pattern, 'https://github.com'))
        self.assertFalse(Origin.match(pattern, 'ftp://github.com'))
        self.assertFalse(Origin.match(pattern, 'http://openplans.github.com'))

    def test_match_subdomains_with_asterisk(self):
        pattern = '*.github.com'
        self.assertFalse(Origin.match(pattern, 'https://github.com'))
        self.assertTrue(Origin.match(pattern, 'http://openplans.github.com'))
        self.assertFalse(Origin.match(pattern, 'http://openplansngithub.com'))

    def test_match_ports_with_asterisk(self):
        pattern = 'localhost:*'
        self.assertFalse(Origin.match(pattern, 'https://github.com'))
        self.assertTrue(Origin.match(pattern, 'http://localhost:8000'))

    def test_match_domains_with_scheme(self):
        pattern = 'http://github.com'
        self.assertFalse(Origin.match(pattern, 'https://github.com'))
        self.assertTrue(Origin.match(pattern, 'http://github.com'))

    def test_lone_asterisk_matches_everything(self):
        pattern = '*'
        self.assertTrue(Origin.match(pattern, 'https://ishkabibble.com:443'))


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

        self.assertIsNotNone(client_auth)
        self.assertTrue(isinstance(client_auth, tuple))
        self.assertEqual(len(client_auth), 2)

    def test_simple_origin_matching_on_not_first_origin(self):
        checker = OriginAuthentication()
        client_auth = checker.check_origin_permission('http://localhost:8000', self.dataset)

        self.assertIsNotNone(client_auth)
        self.assertTrue(isinstance(client_auth, tuple))
        self.assertEqual(len(client_auth), 2)

    def test_unknown_origin(self):
        checker = OriginAuthentication()
        with self.assertRaises(PermissionDenied):
            checker.check_origin_permission('http://toyota.com', self.dataset)
